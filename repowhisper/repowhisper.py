import os
import socketserver
import webbrowser
from http.server import SimpleHTTPRequestHandler

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
            user_level (UserLevel): Default JUNIOR. The user level used to tell the llm how the explanation should be\n
            \tJUNIOR: large explanation 
            \tMID: mid level explanation
            \tSENIOR: very short explanation
        """
        self.source_target = source_target
        self.user_level = user_level
        self.llm = llm

        self._source_manager = SourceManager(self.source_target)
        self._memory_manager = None
        self._repo_path: str | None = None
        self.repo_name: str = source_target.split("/")[-1]

        self._navigator = CodeNavigator(self.llm, self.user_level.value)
        self._architect = Architect(self.llm)
        self._reviewer = Reviewer(self.llm)
        self._storyteller = Storyteller(self.llm, self.user_level.value)

        self._print_ascii_art()

    def _print_ascii_art(self):
        ascii_art = r"""
 ____                                         __                                          
/\  _`\                                      /\ \      __                                 
\ \ \L\ \     __   _____     ___   __  __  __\ \ \___ /\_\    ____  _____      __   _ __  
 \ \ ,  /   /'__`\/\ '__`\  / __`\/\ \/\ \/\ \\ \  _ `\/\ \  /',__\/\ '__`\  /'__`\/\`'__\
  \ \ \\ \ /\  __/\ \ \L\ \/\ \L\ \ \ \_/ \_/ \\ \ \ \ \ \ \/\__, `\ \ \L\ \/\  __/\ \ \/ 
   \ \_\ \_\ \____\\ \ ,__/\ \____/\ \___x___/' \ \_\ \_\ \_\/\____/\ \ ,__/\ \____\\ \_\ 
    \/_/\/ /\/____/ \ \ \/  \/___/  \/__//__/    \/_/\/_/\/_/\/___/  \ \ \/  \/____/ \/_/ 
                     \ \_\                                            \ \_\               
                      \/_/                                             \/_/               
        """
                
        print(f"\033[94m{ascii_art}\033[0m")

    def generate_documentation(self) -> str | None:
        """
        The main public method. Orchestrates cloning, parsing, database building, 
        and fully automated LangGraph analysis.
        
        Returns:
            str | None : A formatted JSON string ready for a frontend UI if there is no error, else it returns None
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
                "tree_structure": "",
                "dependency_graph": {},
                "unprocessed_files": [],
                "current_file": None,
                "current_draft": "",
                "current_line_whispers": [],
                "is_file_reading_error": False,
                "explanations": {},
                "line_whispers": {},
                "file_codes": {},
                "reviewer_feedback": None,
                "final_output_json": ""
            }

            final_state = workflow.graph.invoke(initial_state)
            return final_state["final_output_json"]
        except KeyboardInterrupt:
            print("Program interrupted by the user")
            return None
        finally:
            self._source_manager.cleanup()

    def serve_ui(self, json_data: str|None = None, port: int=8543) -> None:
        """
        Execute full analysis, save data and launch react interface locally.
        """
        if not json_data:
            json_data = self.generate_documentation()
        
            if not json_data:
                print("Impossible to start interface, json generation failed")
                return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_dir = os.path.join(base_dir, "ui_dist")
        
        if not os.path.exists(ui_dir):
            raise FileNotFoundError(
                f"ui_dir not found: {ui_dir}. "
            )

        json_path = os.path.join(ui_dir, "data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_data)

        os.chdir(ui_dir)

        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass
                
        with socketserver.TCPServer(("", port), QuietHandler) as httpd:
            print(f"\nStudio interface available at: http://localhost:{port}")
            print("Press Ctrl+C to stop server and close the app")
            
            webbrowser.open(f"http://localhost:{port}")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n Repowhisper server turned off")
                httpd.server_close()
