import json
import os
import socketserver
import webbrowser
from http.server import SimpleHTTPRequestHandler
from typing import Any

from agents.architect import Architect
from agents.navigator import CodeNavigator
from agents.reviewer import Reviewer
from agents.storyteller import Storyteller
from ingestion.source_manager import SourceManager
from langchain_core.language_models.chat_models import BaseChatModel
from orchestration.state import ProjectState
from orchestration.workflow import AgentsWorkflow
from tqdm import tqdm
from utils.config import UserLevel


class RepoWhisper:
    """
    The main Facade for the Excode library.
    This class orchestrates the entire process from fetching the repository
    to answering complex questions using AI agents.

    It follows the Dependency Inversion Principle by accepting any language
    model that adheres to the BaseChatModel interface.
    """

    def __init__(
        self,
        source_target: str,
        llm: BaseChatModel,
        user_level: UserLevel = UserLevel.JUNIOR,
    ):
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
        The main public method. Orchestrates source retrieval and automated
        LangGraph analysis.

        Returns:
            A formatted JSON string ready for a frontend UI if there is no error, else it returns None
        """
        init_bar = tqdm(
            total=2,
            bar_format="{desc}: {percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            colour="CYAN",
            leave=False
        )
        try:
            init_bar.set_description(f"Cloning repo from {self.source_target}")
            self._repo_path = self._source_manager.get_path()
            init_bar.update(1)

            init_bar.set_description("Preparing analysis workflow")
            init_bar.update(1)
            init_bar.close()

            workflow = AgentsWorkflow(
                root_dir=self._repo_path,
                architect=self._architect,
                navigator=self._navigator,
                reviewer=self._reviewer,
                storyteller=self._storyteller,
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
                "final_output_json": "",
            }

            final_state = workflow.graph.invoke(initial_state)
            return final_state["final_output_json"]
        except KeyboardInterrupt:
            print("Program interrupted by the user")
            return None
        finally:
            self._source_manager.cleanup()

    def serve_ui(
        self,
        json_data: dict[str, Any] | None = None,
        port: int = 8543,
    ) -> None:
        """
        Execute full analysis, save data and launch react interface locally.
        """
        if json_data is None or json_data == "":
            json_content = self.generate_documentation()

            if not json_content:
                print("Impossible to start interface, json generation failed")
                return
        else:
            json_content = json.dumps(json_data)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_dir = os.path.join(base_dir, "ui_dist")

        if not os.path.exists(ui_dir):
            raise FileNotFoundError(f"ui_dir not found: {ui_dir}. ")

        json_path = os.path.join(ui_dir, "data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_content)

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
