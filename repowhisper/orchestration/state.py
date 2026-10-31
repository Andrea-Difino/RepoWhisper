import operator
from typing import Annotated, TypedDict


class ProjectState(TypedDict):
    """
    The global shared state for the RepoWhisper LangGraph orchestration.
    Acts as the central communication blackboard for all agents, ensuring 
    type safety and predictable data flow.
    """

    architecture_summary: str
    dependency_graph: dict[str, list[str]]

    unprocessed_files: list[str]
    current_file: str | None

    explanations: Annotated[dict[str, str], operator.ior]
    reviewer_feedback: str | None
    final_output_json: str

    
