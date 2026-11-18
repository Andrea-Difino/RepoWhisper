__all__ = [
    "InterfaceError",
    "InvalidSourceError",
    "ProviderError",
    "RepoWhisperError",
    "ReportError",
    "ReportFileError",
    "RepositoryCloneError",
    "SourceError",
]


class RepoWhisperError(Exception):
    """Base exception for errors that can be presented to a RepoWhisper user."""


class SourceError(RepoWhisperError):
    """Base exception for repository source errors."""


class InvalidSourceError(SourceError, ValueError):
    """Raised when the repository target is not a supported GitHub URL."""


class RepositoryCloneError(SourceError, RuntimeError):
    """Raised when a GitHub repository cannot be cloned."""


class ProviderError(RepoWhisperError, RuntimeError):
    """Raised when the configured LLM provider rejects or cannot complete a request."""


class ReportError(RepoWhisperError, ValueError):
    """Raised when generated or loaded JSON does not match the report schema."""


class ReportFileError(ReportError, FileNotFoundError):
    """Raised when a report file cannot be found or read."""


class InterfaceError(RepoWhisperError):
    """Raised when the local study interface cannot be started."""
