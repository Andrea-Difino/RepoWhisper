from agents.architect import Architect
from agents.navigator import CodeNavigator
from agents.reviewer import Reviewer
from agents.storyteller import Storyteller
from ingestion.ingestor import Ingestor
from ingestion.source_manager import SourceManager
from langchain_core.language_models.chat_models import BaseChatModel
from memory.chroma_db_manager import ChromaDBManager
from orchestration.state import ProjectState
from orchestration.workflow import AgentsWorkflow
from utils.config import UserLevel


class RepoWhisper:
    """
    The main Facade for the Excode library.
    This class orchestrates the entire process from fetching the repository 
    to answering complex questions using AI agents.
    
    It follows the Dependency Inversion Principle by accepting any language 
    model that adheres to the BaseChatModel interface.
    """

    def __init__(self, source_target: str, llm: BaseChatModel, user_level: UserLevel = UserLevel.JUNIOR):
        """
        Initializes the Excode engine.
        
        Args:
            source_target (str): The URL of the git repository or local path.
            llm (BaseChatModel): The initialized LangChain chat model.
            user_level (UserLevel): Default JUNIOR. The user level used to tell the llm how the explanation should be
                                    JUNIOR: large explanation 
                                    MID: mid level explanation
                                    SENIOR: very short explanation
        """
        self.source_target = source_target
        self.user_level = user_level
        self.llm = llm

        self._source_manager = SourceManager(self.source_target)
        self._memory_manager = None
        self._repo_path = None

        self._navigator = CodeNavigator(self.llm, self.user_level.value)
        self._architect = Architect(self.llm)
        self._reviewer = Reviewer(self.llm)
        self._storyteller = Storyteller(self.llm)

    def generate_documentation(self) -> str:
        """
        The main public method. Orchestrates cloning, parsing, database building, 
        and fully automated LangGraph analysis.
        
        Returns:
            str: A formatted JSON string ready for a frontend UI.
        """
        try:
            self._repo_path = self._source_manager.get_path()
            ingestor = Ingestor(self._repo_path)

            docs = ingestor.ingest()
            if not docs:
                raise RuntimeError("No parsable code found in target source.")

            self._memory_manager = ChromaDBManager(docs)

            workflow = AgentsWorkflow(
                root_dir=self._repo_path,
                memory_manager=self._memory_manager,
                architect=self._architect,
                navigator=self._navigator,
                reviewer=self._reviewer,
                storyteller=self._storyteller
            )

            initial_state: ProjectState = {
                "architecture_summary": "",
                "dependency_graph": {},
                "unprocessed_files": [],
                "current_file": None,
                "current_draft": "",
                "file_error": False,
                "explanations": {},
                "reviewer_feedback": None,
                "final_output_json": ""
            }

            final_state = workflow.graph.invoke(initial_state)
            return final_state["final_output_json"]
            
        finally:
            self._source_manager.cleanup()