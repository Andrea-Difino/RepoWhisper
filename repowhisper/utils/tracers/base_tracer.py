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
    def extract_dependencies(self, file_path: str) -> list[str]:
        """Extract modules names imported inside the file"""

    @abstractmethod
    def resolve_module_to_file(self, module_name: str, valid_files: list[str]) -> str | None:
        """"Convert the language namespace in the actual path""" 
