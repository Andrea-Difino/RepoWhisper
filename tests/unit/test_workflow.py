import json
from types import SimpleNamespace
from typing import Any, cast

import pytest

from repowhisper.orchestration.workflow import AgentsWorkflow


class FakeAgent:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def analyze(self, query, context):
        self.calls.append((query, context))
        return self.response


class FakeLayaReviewer:
    def __init__(self, feedback=None):
        self.feedback = feedback

    def review(self, draft):
        return self.feedback


def make_workflow(tmp_path):
    workflow = cast(Any, AgentsWorkflow.__new__(AgentsWorkflow))
    workflow.root_dir = str(tmp_path)
    workflow.architect = FakeAgent("summary")
    workflow.navigator = FakeAgent(
        {"explanation": "draft", "line_whispers": [{"line_number": 1, "note": "note"}]}
    )
    workflow.reviewer_agent = FakeLayaReviewer()
    workflow.storyteller = FakeAgent("narrative")
    workflow.tracer = SimpleNamespace(
        build_graph=lambda: {"file.py": []},
        get_ordered_processing_list=lambda _graph: ["file.py"],
    )
    workflow.pbar = None
    return workflow


def test_workflow_build_graph_and_architect_tracer_nodes(tmp_path):
    workflow = make_workflow(tmp_path)
    graph = workflow._build_graph()
    assert graph is not None

    result = workflow._node_architect({})
    assert result["architecture_summary"] == "summary"
    workflow._node_tracer({})
    assert workflow.pbar is not None
    workflow.pbar.close()


def test_workflow_dispatch_navigator_reviewer_and_storyteller(tmp_path):
    (tmp_path / "file.py").write_text("value = 1\n", encoding="utf-8")
    workflow = make_workflow(tmp_path)

    selected = workflow._node_dispatcher({"unprocessed_files": ["file.py"]})
    assert selected["current_file"] == "file.py"
    assert selected["unprocessed_files"] == []
    assert workflow._node_dispatcher({"unprocessed_files": []}) == {"current_file": None}

    navigation = workflow._node_navigator(selected)
    assert navigation["file_codes"]["file.py"].strip() == "value = 1"
    reviewed = workflow._node_reviewer(
        {**selected, **navigation, "current_line_whispers": navigation["current_line_whispers"]}
    )
    assert reviewed["explanations"] == {"file.py": "draft"}
    assert reviewed["line_whispers"] == {"file.py": {1: "note"}}

    final = workflow._node_storyteller(
        {
            "architecture_summary": "summary",
            "tree_structure": "tree",
            "explanations": reviewed["explanations"],
            "file_codes": navigation["file_codes"],
            "line_whispers": reviewed["line_whispers"],
        }
    )
    payload = json.loads(final["final_output_json"])
    assert payload["narrative"] == "narrative"
    assert payload["raw_modules"][0]["file"] == "file.py"


def test_workflow_error_and_routing_validation(tmp_path):
    workflow = make_workflow(tmp_path)
    missing = workflow._node_navigator({"current_file": "missing.py", "reviewer_feedback": None})
    assert missing["is_file_reading_error"] is True
    assert workflow._skip_file({"is_file_reading_error": True}) == "file_error"
    assert workflow._skip_file({}) == "no_file_error"
    assert workflow._dispatch_routing({"current_file": "file.py"}) == "process_file"
    assert workflow._dispatch_routing({"current_file": None}) == "finish_analysis"
    assert workflow._review_routing({"reviewer_feedback": "retry"}) == "fail_retry"
    assert workflow._review_routing({"reviewer_feedback": None}) == "pass_next"


@pytest.mark.parametrize(
    "feedback, expected",
    [
        ("fix it", {"reviewer_feedback": "fix it"}),
        (None, {"reviewer_feedback": None}),
    ],
)
def test_laya_reviewer_feedback(tmp_path, feedback, expected):
    workflow = make_workflow(tmp_path)
    workflow.reviewer_agent = FakeLayaReviewer(feedback)
    result = workflow._node_reviewer(
        {"current_draft": "draft", "current_file": "file.py", "current_line_whispers": []}
    )
    assert result.get("reviewer_feedback") == expected["reviewer_feedback"]
