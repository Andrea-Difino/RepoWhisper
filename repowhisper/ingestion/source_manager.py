import tempfile

from git import Repo
from git.exc import GitCommandError

from ..utils.exceptions import InvalidSourceError, RepositoryCloneError


class SourceManager:
    """
    Handles the retrieval and preparation of the source code.
    Responsible for cloning remote repositories.
    """

    def __init__(self, target: str):
        self.target = target
        self.temp_dir = None

    def get_path(self) -> str:
        """
        Clones the repository and return the absolute path to the temp folder.
        
        Returns:
            The absolute path to the ready-to-use source code.
            
        Raises:
            ValueError: If URL is not a valid github URL.
            RuntimeError: If the git cloning process fails.
        """
        if self.target.startswith(("http://github.com/", "https://github.com/")):
            return self._clone_repo()
        else:
            raise InvalidSourceError(
                "The source must be a valid GitHub HTTP(S) repository URL."
            )

    def _clone_repo(self) -> str:
        """
        Creates a temporary directory and clones the git repository into it.
        """
        self.temp_dir = tempfile.TemporaryDirectory(prefix="repowhisper_")
        try:
            Repo.clone_from(self.target, self.temp_dir.name)
            return self.temp_dir.name
        except GitCommandError as e:
            self.cleanup()
            raise RepositoryCloneError(
                "The repository could not be cloned. Check that the URL is correct "
                "and that the repository is public or Git has access to it "
                f"(Git exit code: {e.status})."
            )

    def cleanup(self) -> None:
        """
        Removes temporary directories to free up disk space.
        Should be called in a finally block.
        """
        if self.temp_dir:
            self.temp_dir.cleanup()
            self.temp_dir = None