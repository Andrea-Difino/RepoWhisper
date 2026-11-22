import json

from repo_fixture import make_repo, write

from repowhisper.orchestration.workflow import AgentsWorkflow
from repowhisper.schemas.analysis_schema import AnalysisJsonValidator
from repowhisper.utils.token_budget import estimate_tokens


class Log:
    """Shared, ordered log of every agent call."""

    def __init__(self):
        self.events = []


class FakeNavigator:
    def __init__(self, log, one_liner=True):
        self.log, self.one_liner = log, one_liner
        self.queries = {}

    def analyze(self, query, context):
        name = context.splitlines()[0][:40]
        self.log.events.append("navigator")
        self.queries.setdefault(name, []).append(query)
        out = {
            "explanation": "Reads and transforms data. It also validates it.",
            "line_whispers": [{"line_number": 1, "note": "first line"}],
        }
        if self.one_liner:
            out["one_liner"] = f"Role of {name.strip()}"
        return out


class ScriptedAgent:
    def __init__(self, log, name, responses):
        self.log, self.name, self.responses = log, name, list(responses)
        self.calls = []

    def analyze(self, query, context):
        self.log.events.append(self.name)
        self.calls.append((query, context))
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]


class NoReview:
    def review(self, draft):
        return None


def initial_state():
    return {
        "architecture_summary": "", "tree_structure": "", "tree_prompt": "", "facts_sheet": "",
        "evidence_pack": "", "dependency_graph": {}, "unprocessed_files": [], "current_file": None,
        "current_draft": "", "current_one_liner": "", "current_line_whispers": [],
        "is_file_reading_error": False, "explanations": {}, "one_liners": {}, "line_whispers": {},
        "file_codes": {}, "reviewer_feedback": None, "final_output_json": "",
    }


def run(tmp_path, architect_responses, story_responses, **kwargs):
    log = Log()
    navigator = kwargs.pop("navigator", None) or FakeNavigator(log)
    navigator.log = log
    architect = ScriptedAgent(log, "architect", architect_responses)
    storyteller = ScriptedAgent(log, "storyteller", story_responses)
    workflow = AgentsWorkflow(
        root_dir=str(tmp_path), architect=architect, navigator=navigator,
        storyteller=storyteller, reviewer_agent=NoReview(), **kwargs,
    )
    final = workflow.graph.invoke(initial_state())
    return log, architect, storyteller, navigator, final


def test_architect_and_storyteller_run_after_the_file_analysis_on_grounded_evidence(tmp_path):
    make_repo(tmp_path)
    log, architect, storyteller, navigator, final = run(
        tmp_path,
        architect_responses=["The `Engine` in `app/core.py` is the core."],
        story_responses=["Docs about `Engine` and `app/cli.py`."],
    )

    assert log.events == ["navigator"] * 3 + ["architect", "storyteller"]

    arch_ctx = architect.calls[0][1]
    assert "PROJECT FACTS" in arch_ctx and "DIRECTORY TREE" in arch_ctx and "MODULE NOTES" in arch_ctx
    assert "`app/core.py` (2)" in arch_ctx  # fan-in fact
    assert "Role of" in arch_ctx  # one-liners coming from the Navigator

    story_ctx = storyteller.calls[0][1]
    assert story_ctx.index("PROJECT FACTS") < story_ctx.index("MODULE NOTES") < story_ctx.index("DRAFT ARCHITECTURAL")
    assert "The `Engine` in `app/core.py` is the core." in story_ctx  # the Architect draft is handed over
    assert "`app/util.py`" in story_ctx  # per-file notes now reach the Storyteller

    report = AnalysisJsonValidator.validate_string(final["final_output_json"])
    assert report.narrative.startswith("Docs about")
    assert "app" in report.tree_structure and len(report.raw_modules) == 3


def test_navigator_receives_the_notes_of_already_analysed_dependencies(tmp_path):
    make_repo(tmp_path)
    _, _, _, navigator, _ = run(tmp_path, ["ok"], ["ok"])

    util_queries = next(q for name, q in navigator.queries.items() if "Small utilities" in name or "from app.core" in name)
    assert "already analysed" in util_queries[0] and "app/core.py: Role of" in util_queries[0]
    core_queries = next(q for name, q in navigator.queries.items() if "Core cleaning" in name)
    assert "already analysed" not in core_queries[0]  # core.py has no analysed dependency yet


def test_missing_one_liner_falls_back_to_the_first_sentence_of_the_explanation(tmp_path):
    make_repo(tmp_path)
    log = Log()
    _, architect, _, _, final = run(tmp_path, ["ok"], ["ok"], navigator=FakeNavigator(log, one_liner=False))
    assert "Reads and transforms data." in architect.calls[0][1]
    assert "It also validates it." not in architect.calls[0][1].split("MODULE NOTES")[1]


def test_invented_names_trigger_exactly_one_corrective_regeneration(tmp_path):
    make_repo(tmp_path)
    _, architect, storyteller, _, final = run(
        tmp_path,
        architect_responses=["Uses `PlannerAgent` from `app/planner.py`.", "Uses `Engine` from `app/core.py`."],
        story_responses=["All good with `Engine`."],
    )

    assert len(architect.calls) == 2
    assert "CORRECTION REQUIRED" in architect.calls[1][0] and "`PlannerAgent`" in architect.calls[1][0]
    assert final["architecture_summary"] == "Uses `Engine` from `app/core.py`."
    assert len(storyteller.calls) == 1  # clean text -> zero extra calls
    assert "PlannerAgent" not in storyteller.calls[0][1]  # the bad draft never reaches the Storyteller


def test_retry_keeps_the_answer_with_fewer_unknown_references_and_never_loops(tmp_path):
    make_repo(tmp_path)
    worse, better = "`Ghost1` `Ghost2` `Ghost3`", "`Ghost1`"
    _, architect, _, _, final = run(tmp_path, [worse, better, "never used"], ["ok"])
    assert len(architect.calls) == 2  # one retry at most
    assert final["architecture_summary"] == better

    _, architect, _, _, final = run(tmp_path, [better, worse, "never used"], ["ok"])
    assert final["architecture_summary"] == better  # a worse retry is discarded


def test_small_budget_collapses_notes_with_bounded_calls_and_keeps_the_budget(tmp_path):
    make_repo(tmp_path)
    for d in range(12):
        for f in range(4):
            write(tmp_path / f"pkg{d}" / f"mod{f}.py", f'"""Module {d}.{f}."""\n\n\ndef fn{d}_{f}(x):\n    return x\n')

    summaries = []

    class FakeSummarizer:
        def analyze(self, query, context):
            summaries.append((query, estimate_tokens(context)))
            return f"Summary of {query}"

    budget = 900
    log, architect, storyteller, _, final = run(
        tmp_path, ["ok"], ["ok"], package_summarizer=FakeSummarizer(), context_budget=budget
    )

    assert summaries, "notes did not fit, so directories must have been collapsed"
    assert len(summaries) <= 13 * 2  # O(directories)
    assert all(tokens <= 2500 + 50 for _, tokens in summaries)  # every call is small
    assert estimate_tokens(final["evidence_pack"]) <= budget
    assert estimate_tokens(final["tree_prompt"]) <= budget // 4 + 1
    assert "pkg0" in final["tree_structure"]  # the UI still gets the complete tree
    # architect + storyteller inputs stay O(budget), not O(repo size)
    assert estimate_tokens(architect.calls[0][1]) < budget * 2
    assert estimate_tokens(storyteller.calls[0][1]) < budget * 2


def test_everything_fitting_the_budget_makes_zero_summarizer_calls(tmp_path):
    make_repo(tmp_path)

    class Boom:
        def analyze(self, *a, **k):
            raise AssertionError("must not be called")

    run(tmp_path, ["ok"], ["ok"], package_summarizer=Boom())


def test_final_json_keeps_the_documented_contract(tmp_path):
    make_repo(tmp_path)
    *_, final = run(tmp_path, ["ok"], ["ok"])
    payload = json.loads(final["final_output_json"])
    assert set(payload) == {"title", "tree_structure", "narrative", "raw_modules"}
    assert set(payload["raw_modules"][0]) == {"file", "explanation", "code_snippet", "notes"}
