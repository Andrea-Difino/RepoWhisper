import codecs
import os
import re
from typing import Any, Literal

from agents.architect import Architect
from agents.navigator import CodeNavigator
from agents.package_summarizer import PackageSummarizer
from agents.reviewer import LayaReviewer
from agents.storyteller import Storyteller
from langgraph.graph import END, START, StateGraph
from orchestration.state import LineWhisperData, ProjectState
from tqdm import tqdm
from utils.dependency_tracer import DependencyTracer
from utils.evidence_packer import EvidencePacker, FileCard
from utils.facts_extractor import FactsExtractor
from utils.grounding_verifier import GroundingVerifier
from utils.token_budget import TokenUtilities
from utils.tree_generator import ProjectTreeGenerator


class AgentsWorkflow:
    """
    Constructs and executes the LangGraph state machine for analyzing repositories.

    Pipeline: Tracer -> (Navigator <-> local Laya/Vega Reviewer) per file -> static Facts
    and budgeted evidence -> Architect -> Storyteller. The Architect and the Storyteller
    run AFTER the per-file analysis so they work on grounded evidence instead of on the
    bare directory tree.
    """

    package_summarizer: PackageSummarizer | None = None
    context_budget: int = TokenUtilities.DEFAULT_CONTEXT_BUDGET

    MAX_DEPENDENCY_NOTES = 8

    def __init__(
            self, 
            root_dir: str,
            architect: Architect, 
            navigator: CodeNavigator,
            storyteller: Storyteller,
            reviewer_agent: LayaReviewer,
            package_summarizer: PackageSummarizer | None = None,
            context_budget: int = TokenUtilities.DEFAULT_CONTEXT_BUDGET,
        ):
        self.root_dir = root_dir
        self.package_summarizer = package_summarizer
        self.context_budget = context_budget

        self.architect = architect
        self.navigator = navigator
        self.storyteller = storyteller
        self.reviewer_agent = reviewer_agent
        self.tracer = DependencyTracer(self.root_dir)

        self.pbar: tqdm | None = None
        
        self.graph = self._build_graph()

    def _build_graph(self):
        """Compiles the nodes and edges into a runnable LangGraph application."""
        workflow = StateGraph(ProjectState)

        workflow.add_node("tracer_node", self._node_tracer)
        workflow.add_node("file_dispatcher_node", self._node_dispatcher)
        workflow.add_node("navigator_node", self._node_navigator)
        workflow.add_node("reviewer_node", self._node_reviewer)
        workflow.add_node("facts_node", self._node_facts)
        workflow.add_node("architect_node", self._node_architect)
        workflow.add_node("storyteller_node", self._node_storyteller)

        workflow.add_edge(START, "tracer_node")
        workflow.add_edge("tracer_node", "file_dispatcher_node")

        workflow.add_conditional_edges(
            "file_dispatcher_node",
            self._dispatch_routing,
            {
                "process_file": "navigator_node",
                "finish_analysis": "facts_node"
            }
        )

        workflow.add_conditional_edges(
            "navigator_node",
            self._skip_file,
            {
                "file_error": "file_dispatcher_node",
                "no_file_error": "reviewer_node"
            }
        )

        workflow.add_conditional_edges(
            "reviewer_node",
            self._review_routing,
            {
                "fail_retry": "navigator_node", 
                "pass_next": "file_dispatcher_node"
            }
        )

        workflow.add_edge("facts_node", "architect_node")
        workflow.add_edge("architect_node", "storyteller_node")
        workflow.add_edge("storyteller_node", END)

        return workflow.compile()


    def _node_facts(self, state: ProjectState) -> dict:
        """
        Zero-token node: extracts verifiable facts from the code and packs the per-file
        notes into a text that fits the token budget (collapsing directories with a few
        small LLM calls only if the notes do not fit).
        """
        if self.pbar:
            self.pbar.set_description("Codebase analyzed")
            self.pbar.close()

        explanations = state.get("explanations", {})
        files = list(explanations)
        one_liners = state.get("one_liners", {})

        facts = FactsExtractor(self.root_dir).extract(files, state.get("dependency_graph", {}))

        cards = []
        for path in files:
            file_facts = facts.files[path]
            summary = (
                one_liners.get(path)
                or file_facts.docstring
                or self._fallback_one_liner(explanations[path])
            )
            cards.append(
                FileCard(
                    path=path,
                    summary=summary,
                    symbols=tuple(file_facts.symbols),
                    deps=tuple(facts.graph.get(path, [])),
                    rank=facts.rank.get(path, 0.0),
                )
            )

        tree_structure = ProjectTreeGenerator.generate(self.root_dir)
        tree_limit = max(self.context_budget // 4, 1)
        tree_prompt = (
            tree_structure
            if TokenUtilities.estimate_tokens(tree_structure) <= tree_limit
            else ProjectTreeGenerator.generate_within_budget(self.root_dir, tree_limit)
        )

        pack_budget = max(
            self.context_budget - TokenUtilities.estimate_tokens(facts.sheet) - TokenUtilities.estimate_tokens(tree_prompt),
            self.context_budget // 3,
        )
        summarizer = self.package_summarizer.analyze if self.package_summarizer else None
        evidence_pack = EvidencePacker(summarizer=summarizer).pack(cards, pack_budget)

        return {
            "tree_structure": tree_structure,
            "tree_prompt": tree_prompt,
            "repo_facts": facts,
            "facts_sheet": facts.sheet,
            "evidence_pack": evidence_pack,
        }

    def _node_architect(self, state: ProjectState) -> dict:
        tree = state.get("tree_prompt") or state.get("tree_structure")
        if tree is None:
            tree = ProjectTreeGenerator.generate(self.root_dir)

        sections = []
        if state.get("facts_sheet"):
            sections.append(state["facts_sheet"])
        if tree.strip():
            sections.append(f"DIRECTORY TREE:\n{tree}")
        if state.get("evidence_pack"):
            sections.append(
                "MODULE NOTES (grouped by directory; each note is derived from the file's code):\n"
                + state["evidence_pack"]
            )
        context = "\n\n".join(sections)

        query = "Analyze the project evidence and provide an executive architectural summary."
        summary = self._generate_grounded(
            self.architect, query, context, state, evidence_text=context, label="Architect"
        )

        update: dict[str, Any] = {"architecture_summary": summary}
        if "tree_structure" not in state:
            update["tree_structure"] = tree
        return update

    def _node_tracer(self, state: ProjectState) -> dict:
        deps = self.tracer.build_graph()

        raw_ordered_files = self.tracer.get_ordered_processing_list(deps)
        ordered_files = [f for f in raw_ordered_files if not f.endswith("__init__.py")]

        total_files = len(ordered_files)
        self.pbar = tqdm(
            total=total_files, 
            desc="Analyzing files", 
            bar_format="{desc}: {percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            colour="CYAN"
        )

        return {
            "dependency_graph": deps,
            "unprocessed_files": ordered_files,
            "explanations": {},
            "one_liners": {},
            "line_whispers": {}
        }

    def _node_dispatcher(self, state: ProjectState) -> dict:
        """Pops the next file from the queue."""
        unprocessed = state.get("unprocessed_files", [])
        if not unprocessed:
            return {"current_file": None}
            
        next_file = unprocessed[0]
        return {
            "current_file": next_file,
            "unprocessed_files": unprocessed[1:],
            "reviewer_feedback": None,
            "current_line_whispers": [],
            "current_one_liner": "",
            "file_error": False,
        }

    def _node_navigator(self, state: ProjectState) -> dict:
        file_target = state["current_file"]
        feedback = state.get("reviewer_feedback")

        if self.pbar:
            self.pbar.set_description(f"Navigator reading: {os.path.basename(file_target)}") # type: ignore

        absolute_target = os.path.normpath(os.path.join(self.root_dir, file_target)) # type: ignore
        code_context = ""
        try:
            with codecs.open(absolute_target, 'r', encoding='utf-8', errors='ignore') as f:
                code_context = f.read()
        except OSError as e:
            tqdm.write(f"⚠️ Error reading file {absolute_target}: {e}")
            if self.pbar:
                self.pbar.update(1)
            return {"is_file_reading_error": True}

        query = (
            f"Explain the logic of this file. Follow this feedback strictly: {feedback}" 
            if feedback 
            else "Explain this file logically."
        )
        dependency_notes = self._dependency_notes(state, file_target)
        if dependency_notes:
            query = f"{query}\n\n{dependency_notes}"
        navigation = self.navigator.analyze(query, context=code_context)
        if not isinstance(navigation, dict):
            raise TypeError("Code Navigator must return a structured dictionary.")

        explanation = navigation.get("explanation")
        raw_line_whispers = navigation.get("line_whispers")
        if not isinstance(explanation, str) or not isinstance(raw_line_whispers, list):
            raise TypeError(
                "Code Navigator response must contain an explanation and a line_whispers list."
            )

        line_count = len(code_context.splitlines())
        line_whispers: list[LineWhisperData] = []
        for whisper in raw_line_whispers:
            if not isinstance(whisper, dict):
                raise TypeError("Each Code Navigator line whisper must be an object.")

            line_number = whisper.get("line_number")
            note = whisper.get("note")
            if (
                not isinstance(line_number, int)
                or not isinstance(note, str)
                or not note.strip()
                or not 1 <= line_number <= line_count
            ):
                raise ValueError(
                    "Code Navigator line whispers must contain a valid 1-based line number and note."
                )

            line_whispers.append({"line_number": line_number, "note": note.strip()})

        one_liner = navigation.get("one_liner")
        one_liner = (
            " ".join(one_liner.split()[:30])
            if isinstance(one_liner, str) and one_liner.strip()
            else self._fallback_one_liner(explanation)
        )

        return {
            "current_draft": explanation, 
            "current_one_liner": one_liner,
            "current_line_whispers": line_whispers,
            "is_file_reading_error": False, 
            "file_codes": {file_target:code_context}
        }

    def _node_reviewer(self, state: ProjectState) -> dict:
        """Deterministic System-One review via calibrated Laya/Vega."""
        draft = state.get("current_draft", "")
        file_target = state["current_file"]
        if self.pbar:
            self.pbar.set_description(f"Reviewer checking: {os.path.basename(file_target)}") # type: ignore

        feedback = self.reviewer_agent.review(draft)

        if feedback is not None:
            if self.pbar:
                self.pbar.set_description(
                    f"Laya rejected {os.path.basename(file_target)} " # type: ignore
                )
            return {"reviewer_feedback": feedback}

        if self.pbar:
            self.pbar.update(1)

        return {
            "explanations": {file_target: draft},
            "one_liners": {
                file_target: state.get("current_one_liner") or self._fallback_one_liner(draft)
            },
            "line_whispers": {
                file_target: {
                    whisper["line_number"] - 1: whisper["note"]
                    for whisper in state.get("current_line_whispers", [])
                }
            },
            "reviewer_feedback": None,
        }
    
    def _node_storyteller(self, state: ProjectState) -> dict:
        sections = []
        if state.get("facts_sheet"):
            sections.append(state["facts_sheet"])
        if state.get("evidence_pack"):
            sections.append(
                "MODULE NOTES (grouped by directory; each note is derived from the file's code):\n"
                + state["evidence_pack"]
            )
        sections.append(
            "DRAFT ARCHITECTURAL OVERVIEW (written from the evidence above):\n"
            + state.get("architecture_summary", "")
        )
        raw_context = "\n\n".join(sections)

        # The draft overview is NOT accepted as evidence: only the facts, the notes and the tree are.
        evidence_text = "\n".join(
            [state.get("tree_prompt", ""), state.get("facts_sheet", ""), state.get("evidence_pack", "")]
        )
        narrative_markdown = self._generate_grounded(
            self.storyteller,
            query=(
                "Generate the final cohesive documentation.\n\n"
                "Reminder: mention only files, classes, functions, libraries and flags that appear in "
                "the evidence above, each one inside `backticks`; leave out anything that is not there."
            ),
            context=raw_context,
            state=state,
            evidence_text=evidence_text,
            label="Storyteller",
        )

        raw_modules_list = []
        for file_target, expl in state.get("explanations", {}).items():
            raw_modules_list.append({
                "file": file_target,
                "explanation": expl,
                "code_snippet": state.get("file_codes", {}).get(file_target, ""),
                "notes": state.get("line_whispers", {}).get(file_target, {})
            })

        final_data = {
            "title": "RepoWhisper Analysis",
            "tree_structure": state.get("tree_structure", ""),
            "narrative": narrative_markdown,
            "raw_modules": raw_modules_list
        }

        import json
        return {"final_output_json": json.dumps(final_data, indent=2)}

    def _generate_grounded(
        self,
        agent: Any,
        query: str,
        context: str,
        state: ProjectState,
        evidence_text: str,
        label: str,
    ) -> str:
        """
        Runs an agent and checks its code references against the repository facts.
        If invented names are found, it regenerates ONCE with a correction note; the
        better of the two answers is kept. Costs 0 extra calls when the text is clean.
        """
        text = agent.analyze(query=query, context=context)

        facts = state.get("repo_facts")
        if facts is None:
            return text

        verifier = GroundingVerifier(facts, evidence_text)
        report = verifier.verify(text)
        if report.ok:
            return text

        tqdm.write(
            f"{label}: {len(report.unknown)} code reference(s) not found in the repository "
            f"({', '.join(report.unknown[:5])}). Regenerating once."
        )
        retry_text = agent.analyze(query=f"{query}\n\n{report.feedback()}", context=context)
        retry_report = verifier.verify(retry_text)
        if len(retry_report.unknown) <= len(report.unknown):
            text, report = retry_text, retry_report

        if report.unknown:
            tqdm.write(
                f"{label}: unverified references remain: {', '.join(report.unknown[:8])}"
            )
        return text

    def _dependency_notes(self, state: ProjectState, file_target: str) -> str:
        """One-line notes of the already-analysed modules imported by `file_target`."""
        graph = state.get("dependency_graph") or {}
        notes = state.get("one_liners") or {}
        lines = []
        for dep in dict.fromkeys(graph.get(file_target, [])):
            if dep != file_target and notes.get(dep):
                lines.append(f"- {dep}: {notes[dep]}")
            if len(lines) >= self.MAX_DEPENDENCY_NOTES:
                break
        if not lines:
            return ""
        return (
            "For context only, this file imports the following modules, which were already analysed "
            "(do not explain them and do not describe anything that is not in the code below):\n"
            + "\n".join(lines)
        )

    @staticmethod
    def _fallback_one_liner(text: str, max_words: int = 25) -> str:
        """First sentence of a text, shortened. Used when the model returns no one-liner."""
        clean = re.sub(r"[*_`#]", "", text or "").strip()
        if not clean:
            return ""
        first = re.split(r"(?<=[.!?])\s", clean, maxsplit=1)[0]
        words = first.split()
        return " ".join(words[:max_words]) + ("…" if len(words) > max_words else "")

    def _skip_file(self, state: ProjectState) -> Literal["file_error", "no_file_error"]:
        if state.get("is_file_reading_error"):
            return "file_error"
        return "no_file_error"

    def _dispatch_routing(self, state: ProjectState) -> Literal["process_file", "finish_analysis"]:
        if state.get("current_file"):
            return "process_file"
        return "finish_analysis"

    def _review_routing(self, state: ProjectState) -> Literal["fail_retry", "pass_next"]:
        if state.get("reviewer_feedback"):
            return "fail_retry"
        return "pass_next"