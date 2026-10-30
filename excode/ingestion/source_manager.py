import os
import tempfile

from git import Repo
from git.exc import GitCommandError


class SourceManager:
    """
    Handles the retrieval and preparation of the source code.
    Responsible for cloning remote repositories or validating local paths.
    """

    def __init__(self, target: str):
        self.target = target
        self.temp_dir = None

    def get_path(self) -> str:
        """
        Returns the local path to the source code.
        Clones the repository if the target is a remote URL.
        
        Returns:
            str: The absolute path to the ready-to-use source code.
            
        Raises:
            ValueError: If the local path does not exist.
            RuntimeError: If the git cloning process fails.
        """
        if self.target.startswith(("http://", "https://")):
            return self._clone_repo()

        if os.path.exists(self.target):
            return self.target

        raise ValueError(f"Target path {self.target} does not exist.")

    def _clone_repo(self) -> str:
        """
        Creates a temporary directory and clones the git repository into it.
        """
        self.temp_dir = tempfile.TemporaryDirectory()
        try:
            print(f"Cloning repository from {self.target}...")
            Repo.clone_from(self.target, self.temp_dir.name)
            return self.temp_dir.name
        except GitCommandError as e:
            self.cleanup()
            raise RuntimeError(
                f"Failed to clone repository. It might be private or non-existent. "
                f"Git exit code: {e.status}"
            )

    def cleanup(self) -> None:
        """
        Removes temporary directories to free up disk space.
        Should be called in a finally block.
        """
        if self.temp_dir:
            self.temp_dir.cleanup()
            self.temp_dir = None