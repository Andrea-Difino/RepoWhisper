import functools
import os
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from agents.architect import Architect
from agents.navigator import CodeNavigator
from agents.reviewer import LayaReviewer
from agents.storyteller import Storyteller
from ingestion.source_manager import SourceManager
from langchain_core.language_models.chat_models import BaseChatModel
from orchestration.state import ProjectState
from orchestration.workflow import AgentsWorkflow
from schemas.analysis_schema import AnalysisJsonValidator
from utils.config import UserLevel
from utils.exceptions import InterfaceError, RepoWhisperError


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
        self._print_ascii_art()

        self.source_target = source_target
        self.user_level = user_level
        self.llm = llm

        self._source_manager = SourceManager(self.source_target)
        self._repo_path: str | None = None

        self._navigator = CodeNavigator(self.llm, self.user_level.value)
        self._architect = Architect(self.llm, self.user_level.value)
        self._reviewer = LayaReviewer()
        self._storyteller = Storyteller(self.llm, self.user_level.value)
        

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
        try:
            print(f"Cloning repo from {self.source_target}")
            self._repo_path = self._source_manager.get_path()

            workflow = AgentsWorkflow(
                root_dir=self._repo_path,
                architect=self._architect,
                navigator=self._navigator,
                storyteller=self._storyteller,
                reviewer_agent=self._reviewer
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

            raw_json = final_state["final_output_json"]
            
            _ = AnalysisJsonValidator.validate_string(raw_json)

            return final_state["final_output_json"]
        except KeyboardInterrupt:
            print("\nProgram interrupted by the user")
            return None
        except RepoWhisperError:
            raise
        except (TypeError, ValueError) as exc:
            raise RepoWhisperError(
                f"The repository analysis could not produce a valid result: {exc}"
            ) from exc
        finally:
            self._source_manager.cleanup()

    def serve_ui(
        self,
        json_path: str | Path | None = None,
        port: int = 8543,
    ) -> None:
        """
        Execute full analysis if json_path is None, save data and launch react interface locally. If json_path is passed the analysis is not executed and the interface starts immediately

        Args:
            json_path (str | Path | None): JSON file path of a previous analysis.
            port (int): port value for the web interface.
        """
        if json_path is None or str(json_path).strip() == "":
            try:
                json_content = self.generate_documentation()
            except KeyboardInterrupt:
                return

            if not json_content:
                return
        else:
            report = AnalysisJsonValidator.validate_file(json_path)
            json_content = report.model_dump_json(indent=2)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_dir = os.path.join(base_dir, "ui_dist")

        if not os.path.exists(ui_dir):
            raise InterfaceError(
                f"The bundled web interface was not found: {ui_dir}. "
                "Reinstall RepoWhisper or verify the package installation."
            )

        output_json_path = os.path.join(ui_dir, "data.json")
        try:
            with open(output_json_path, "w", encoding="utf-8") as f:
                f.write(json_content)
        except OSError as e:
            raise InterfaceError(
                f"Failed to write analysis data to {output_json_path}: {e}"
            ) from e

        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

        handler = functools.partial(QuietHandler, directory=ui_dir)

        try:
            httpd = ThreadingHTTPServer(("", port), handler)
        except OSError as e:
            raise InterfaceError(
                f"Could not start web interface on port {port} (already in use?): {e}"
            ) from e

        with httpd:
            url = f"http://localhost:{port}"
            print(f"\nStudy interface available at: {url}")
            print("Press Ctrl+C to stop server and close the app")

            webbrowser.open(url)

            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nRepoWhisper server turned off")
