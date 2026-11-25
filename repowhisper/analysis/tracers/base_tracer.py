from abc import ABC, abstractmethod


class BaseLanguageTracer(ABC):
    """
    Base interface for the extraction of the dependencies
    """

    @property
    @abstractmethod
    def extension(self) -> str:
        """Return the file extension handled by the specific tracer"""

    @abstractmethod
    def is_useless(self, filename: str) -> bool:
        """Define if a file must be ignored"""

    @abstractmethod
    def extract_dependencies(self, file_path: str, root_dir: str) -> list[str]:
        """Extract modules names imported inside the file"""

    @abstractmethod
    def build_module_index(self, valid_files: list[str]) -> dict[str, str]:
        """
        Create an O(1) index which maps logic modules names to phisical files.
        Es: 'util.console' -> 'src/utils/console.py'
        """

    @abstractmethod
    def resolve_module_to_file(
        self, module_name: str, module_index: dict[str, str]
    ) -> str | None:
        """Use the index to retrieve the actual module path"""
