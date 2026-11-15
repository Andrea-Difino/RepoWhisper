import operator
from typing import Annotated, TypedDict


class LineWhisperData(TypedDict):
    line_number: int
    note: str


class ProjectState(TypedDict):
    """
    The global shared state for the RepoWhisper LangGraph orchestration.
    Acts as the central communication blackboard for all agents, ensuring 
    type safety and predictable data flow.
    """

    architecture_summary: str
    tree_structure: str
    dependency_graph: dict[str, list[str]]

    unprocessed_files: list[str]
    current_file: str | None
    current_draft: str
    current_line_whispers: list[LineWhisperData]
    is_file_reading_error: bool

    explanations: Annotated[dict[str, str], operator.ior]
    line_whispers: Annotated[dict[str, dict[int, str]], operator.ior]
    file_codes: Annotated[dict[str, str], operator.ior]

    reviewer_feedback: str | None
    final_output_json: str

    
