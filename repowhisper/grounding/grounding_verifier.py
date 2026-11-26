import builtins
import keyword
import re
import sys
from dataclasses import dataclass

from ..analysis.facts_extractor import RepoFacts

_FENCED_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
_CHECKABLE_RE = re.compile(r"[-A-Za-z_./][\w\-./:]*(?:\(\))?")
_WORD_RE = re.compile(r"[A-Za-z_][\w\-]*")

_FILE_EXTENSIONS = {
    "py", "pyi", "md", "rst", "txt", "toml", "yaml", "yml", "json", "lock", "cfg", "ini",
    "ts", "tsx", "js", "jsx", "css", "html", "png", "svg", "npz", "sh", "env",
}

_COMMON_TERMS = {
    "pip", "uv", "git", "python", "python3", "pytest", "docker", "npm", "pnpm", "yarn",
    "node", "bash", "sh", "http", "https", "json", "yaml", "toml", "markdown", "html",
    "css", "api", "cli", "ui", "llm", "llms", "ast", "dag", "url", "utf-8", "utf8", "id",
}


@dataclass(frozen=True)
class GroundingReport:
    """Outcome of verifying a generated text against the repository vocabulary."""

    checked: int
    unknown: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.unknown

    def feedback(self) -> str:
        """A correction note to append to the query when regenerating the text."""
        shown = ", ".join(f"`{item}`" for item in self.unknown[:12])
        return (
            "CORRECTION REQUIRED: these code references were not found anywhere in the "
            f"repository evidence: {shown}. Remove them, or replace them with names that "
            "appear verbatim in the evidence. Do not invent replacements."
        )


class GroundingVerifier:
    """
    Checks that every code reference (text in `backticks`) in a generated document
    really exists in the repository.

    It is a pure-Python existence check, like the "existence ratio" used to evaluate
    documentation generators: it catches invented file names, classes, functions,
    libraries, flags and environment variables. It does NOT judge whether a
    description of behaviour is correct.

    Complexity: O(L) in the length of the text, each lookup is O(1) on hash sets.
    """

    def __init__(self, facts: RepoFacts, evidence_text: str = ""):
        """
        Args:
            facts (RepoFacts): full vocabulary extracted from the repository.
            evidence_text (str): the evidence shown to the LLM; any word appearing in it
                is also accepted (e.g. names coming from the module notes).
        """
        self._known = set(facts.known_identifiers)
        self._known |= set(_WORD_RE.findall(evidence_text))
        self._known |= {w.replace("-", "_") for w in self._known if "-" in w}
        self._known |= set(dir(builtins)) | set(keyword.kwlist) | set(sys.stdlib_module_names)
        self._known |= _COMMON_TERMS
        self._known_lower = {w.lower() for w in self._known}

        self._flags = set(facts.known_flags)
        self._paths = set(facts.known_paths)
        self._path_suffixes: set[str] = set()
        for path in self._paths:
            parts = path.split("/")
            for i in range(len(parts)):
                self._path_suffixes.add("/".join(parts[i:]))

    def verify(self, text: str) -> GroundingReport:
        """
        Args:
            text (str): generated markdown.

        Returns:
            GroundingReport: how many references were checked and which are unknown.
        """
        without_fences = _FENCED_BLOCK_RE.sub("", text)
        seen: dict[str, None] = {}
        for match in _CODE_SPAN_RE.finditer(without_fences):
            seen[match.group(1).strip()] = None

        checked = 0
        unknown: list[str] = []
        for span in seen:
            if not self._is_checkable(span):
                continue
            checked += 1
            if not self._is_known(span):
                unknown.append(span)
        return GroundingReport(checked=checked, unknown=tuple(unknown))

    @staticmethod
    def _is_checkable(span: str) -> bool:
        if len(span) < 2 or not _CHECKABLE_RE.fullmatch(span):
            return False
        return any(ch.isalpha() for ch in span)

    def _is_known(self, span: str) -> bool:
        token = span.removesuffix("()").rstrip(".:")
        if not token or token in self._known or token in self._paths or token in self._flags:
            return True
        if token.lower() in self._known_lower:
            return True

        if token.startswith("-"):
            return token.split("=")[0] in self._flags

        if token.startswith(".") and token.lstrip(".") in _FILE_EXTENSIONS:
            return True

        if "/" in token or self._looks_like_filename(token):
            return self._path_known(token)

        segments = [s for s in re.split(r"[.:]", token) if s]
        return all(seg in self._known or seg.lower() in self._known_lower for seg in segments)

    @staticmethod
    def _looks_like_filename(token: str) -> bool:
        stem, dot, ext = token.rpartition(".")
        return bool(dot and stem and ext.lower() in _FILE_EXTENSIONS)

    def _path_known(self, token: str) -> bool:
        normalized = token.strip("/")
        if normalized in self._path_suffixes or normalized.removeprefix("./") in self._path_suffixes:
            return True
        # allow an extension-less module reference such as `agents/architect`
        return any(normalized + ext in self._path_suffixes for ext in (".py", ".md", ".toml"))
