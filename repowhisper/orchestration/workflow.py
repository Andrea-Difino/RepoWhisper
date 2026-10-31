import json
from typing import Literal

from agents.architect import Architect
from agents.navigator import CodeNavigator
from langgraph.graph import END, START, StateGraph
from memory.chroma_db_manager import ChromaDBManager
from orchestration.state import ProjectState

#TODO from agents.reviewer import Reviewer
#TODO from agents.storyteller import Storyteller
from utils.dependency_tracer import DependencyTracer


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

        workflow.add_edge("navigator_node", "reviewer_node")

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
        print("🏗️ Architect is analyzing the project structure")

        summary = self.architect.analyze("Analyze the structure", context="Tree data...")
        return {"architecture_summary": summary}

    def _node_tracer(self, state: ProjectState) -> dict:
        print("🗺️ Tracer is building the logical bottom-up map...")
        deps = self.tracer.build_graph()
        ordered_files = self.tracer.get_ordered_processing_list(deps)
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
            "reviewer_feedback": None
        }

    def _node_navigator(self, state: ProjectState) -> dict:
        file_target = state["current_file"]
        feedback = state.get("reviewer_feedback")
        print(f"🧭 Navigator is reading {file_target}...")
        
        results = self.memory_manager.db.similarity_search(
            query="Extract entire file logic", 
            k=5, 
            filter={"source": file_target} # type: ignore
        )
        
        code_context = "\n".join([doc.page_content for doc in results])
        query = f"Explain the logic of this file. Feedback to fix: {feedback}" if feedback else "Explain this file logically."
        explanation = self.navigator.analyze(query, context=code_context)

        return {"current_draft": explanation}

    def _node_reviewer(self, state: ProjectState) -> dict:
        draft = state.get("current_draft", "")
        file_target = state["current_file"]
        print(f"🛡️ Reviewer is checking {file_target} for debugging violations...")
        
        evaluation = self.reviewer.analyze("Does this explain or debug?", context=draft)

        if "VIOLATION" in evaluation:
            print("❌ Reviewer rejected the explanation. Sending back...")
            return {"reviewer_feedback": evaluation}
        
        print("✅ Reviewer approved the explanation.")

        return {"explanations": {file_target: draft}}

    def _node_storyteller(self, state: ProjectState) -> dict:
        print("📝 Storyteller is generating the final UI JSON...")

        final_data = {
            "title": "RepoWhisper Analysis",
            "architecture": state["architecture_summary"],
            "modules": [{"file": k, "explanation": v} for k, v in state["explanations"].items()]
        }
        return {"final_output_json": json.dumps(final_data, indent=2)}

    

    def _dispatch_routing(self, state: ProjectState) -> Literal["process_file", "finish_analysis"]:
        if state.get("current_file"):
            return "process_file"
        return "finish_analysis"

    def _review_routing(self, state: ProjectState) -> Literal["fail_retry", "pass_next"]:
        if state.get("reviewer_feedback"):
            return "fail_retry"
        return "pass_next"