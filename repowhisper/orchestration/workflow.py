import codecs
import os
from typing import Literal

from agents.architect import Architect
from agents.navigator import CodeNavigator
from agents.reviewer import Reviewer
from agents.storyteller import Storyteller
from langgraph.graph import END, START, StateGraph
from memory.chroma_db_manager import ChromaDBManager
from orchestration.state import ProjectState
from tqdm import tqdm
from utils.dependency_tracer import DependencyTracer
from utils.tree_generator import ProjectTreeGenerator


class AgentsWorkflow:
    """
    Constructs and executes the LangGraph state machine for analyzing repositories.
    Connects the Architect, Tracer, Navigator, Reviewer, and Storyteller in a resilient loop.
    """

    def __init__(
            self, 
            root_dir: str,
            memory_manager: ChromaDBManager,
            architect: Architect, 
            navigator: CodeNavigator, 
            reviewer: Reviewer, 
            storyteller: Storyteller):
        self.root_dir = root_dir

        self.memory_manager = memory_manager

        self.architect = architect
        self.navigator = navigator
        self.reviewer = reviewer
        self.storyteller = storyteller
        self.tracer = DependencyTracer(self.root_dir)

        self.pbar = None

        self.graph = self._build_graph()

    def _build_graph(self):
        """Compiles the nodes and edges into a runnable LangGraph application."""
        workflow = StateGraph(ProjectState)

        workflow.add_node("architect_node", self._node_architect)
        workflow.add_node("tracer_node", self._node_tracer)
        workflow.add_node("file_dispatcher_node", self._node_dispatcher)
        workflow.add_node("navigator_node", self._node_navigator)
        workflow.add_node("reviewer_node", self._node_reviewer)
        workflow.add_node("storyteller_node", self._node_storyteller)

        workflow.add_edge(START, "architect_node")
        workflow.add_edge("architect_node", "tracer_node")
        workflow.add_edge("tracer_node", "file_dispatcher_node")

        workflow.add_conditional_edges(
            "file_dispatcher_node",
            self._dispatch_routing,
            {
                "process_file": "navigator_node",
                "finish_analysis": "storyteller_node"
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

        workflow.add_edge("storyteller_node", END)

        return workflow.compile()


    def _node_architect(self, state: ProjectState) -> dict:
        tree_structure = ProjectTreeGenerator.generate(self.root_dir)
        
        query = "Analyze the project structure and provide an executive architectural summary."
        summary = self.architect.analyze(query, context=tree_structure)
        return {"architecture_summary": summary,  "tree_structure": tree_structure}

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
            "explanations": {}
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
            return {"file_error": True}

        query = f"Explain the logic of this file. Feedback to fix: {feedback}" if feedback else "Explain this file logically."
        explanation = self.navigator.analyze(query, context=code_context)

        #print(explanation)
        return {
            "current_draft": explanation, 
            "file_error": False, 
            "file_codes": {file_target:code_context}
        }

    def _node_reviewer(self, state: ProjectState) -> dict:
        draft = state.get("current_draft", "")
        file_target = state["current_file"]

        evaluation = self.reviewer.analyze("Does this explain or debug?", context=draft)

        clean_str = evaluation.strip()
        if clean_str.startswith("```json"):
            clean_str = clean_str[7:]
        elif clean_str.startswith("```"):
            clean_str = clean_str[3:]

        clean_str = clean_str.removesuffix("```")

        import json
        try:
            result: dict = json.loads(clean_str)
            status = result.get("response", "VIOLATION")
            feedback = result.get("feedback", "")
        except json.JSONDecodeError:
            status = "VIOLATION"
            feedback = ""

        if status == "VIOLATION":
            tqdm.write(f"❌ Reviewer rejected {os.path.basename(file_target)}. Retrying...") #type: ignore
            return {"reviewer_feedback": feedback}

        if self.pbar:
            self.pbar.update(1)

        return {
            "explanations": {file_target: draft},
            "reviewer_feedback": None
        }

    def _node_storyteller(self, state: ProjectState) -> dict:
        if self.pbar:
            self.pbar.set_description("Codebase analyzed")
            self.pbar.close()
        
        print("📝 Storyteller is generating the final UI JSON...")

        raw_context = f"Architecture:\n{state['architecture_summary']}\n"

        narrative_markdown = self.storyteller.analyze(
            query="Generate the final cohesive documentation.", 
            context=raw_context
        )

        raw_modules_list = []
        for file_target, expl in state.get("explanations", {}).items():
            raw_modules_list.append({
                "file": file_target,
                "explanation": expl,
                "code_snippet": state.get("file_codes", {}).get(file_target, "")
            })

        final_data = {
            "title": "RepoWhisper Analysis",
            "tree_structure": state.get("tree_structure", ""),
            "narrative": narrative_markdown,
            "raw_modules": raw_modules_list
        }

        import json
        return {"final_output_json": json.dumps(final_data, indent=2)}

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