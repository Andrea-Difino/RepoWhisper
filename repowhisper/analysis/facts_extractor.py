import ast
import os
import posixpath
import re
import sys
import tomllib
from dataclasses import dataclass, field

_FLAG_RE = re.compile(r"-{1,2}[A-Za-z][\w\-]*")
_ENV_RE = re.compile(r"[A-Z][A-Z0-9_]{2,}")
_DEP_NAME_RE = re.compile(r"\s*([A-Za-z0-9][A-Za-z0-9._\-]*)")

_WALK_IGNORE = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    ".idea",
    ".vscode",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}
_MAX_WALKED_ENTRIES = 50_000

_MAX_SYMBOLS_PER_FILE = 10
_MAX_METHODS_PER_CLASS = 6
_MAX_ARGS_PER_FUNCTION = 5


def pagerank(
    graph: dict[str, list[str]],
    damping: float = 0.85,
    iterations: int = 50,
    tolerance: float = 1e-9,
) -> dict[str, float]:
    """
    Plain power-iteration PageRank (no external dependency).

    An edge A -> B means "A imports B", so rank flows towards the modules that many
    other modules depend on: the structural core of the project.

    Args:
        graph (dict[str, list[str]]): adjacency list (file -> files it imports).
        damping (float): classic PageRank damping factor.
        iterations (int): maximum number of iterations.
        tolerance (float): early-stop threshold on the L1 change between iterations.

    Returns:
        dict[str, float]: rank per node, summing to ~1.0.
    """
    nodes = list(graph)
    n = len(nodes)
    if n == 0:
        return {}

    outgoing = {
        node: [t for t in dict.fromkeys(graph[node]) if t in graph] for node in nodes
    }
    rank = dict.fromkeys(nodes, 1.0 / n)

    for _ in range(iterations):
        dangling = sum(rank[node] for node in nodes if not outgoing[node])
        base = (1.0 - damping) / n + damping * dangling / n
        new_rank = dict.fromkeys(nodes, base)
        for node in nodes:
            targets = outgoing[node]
            if targets:
                share = damping * rank[node] / len(targets)
                for target in targets:
                    new_rank[target] += share
        delta = sum(abs(new_rank[node] - rank[node]) for node in nodes)
        rank = new_rank
        if delta < tolerance:
            break

    return rank


@dataclass
class FileFacts:
    """Facts extracted from one source file with a single AST pass."""

    path: str
    docstring: str = ""
    symbols: list[str] = field(default_factory=list) #each string is a class with its methods or a function with its arguments
    external_imports: set[str] = field(default_factory=set)
    has_main_guard: bool = False


@dataclass
class RepoFacts:
    """
    Everything RepoWhisper can state about a repository without calling an LLM.

    `sheet` is a short human/LLM readable rendering; the `known_*` sets are the full,
    untruncated vocabulary of the repository used to verify generated text.
    """

    files: dict[str, FileFacts]
    graph: dict[str, list[str]]
    rank: dict[str, float]
    fan_in: dict[str, int]
    sheet: str
    known_identifiers: frozenset[str]
    known_paths: frozenset[str]
    known_flags: frozenset[str]


class FactsExtractor:
    """
    Extracts verifiable facts from a Python repository using only static analysis.

    The output grounds the LLM agents (what really exists in the project) and feeds the
    deterministic verifier that checks the generated documentation.
    """

    MAX_LIST_ITEMS = 12
    MAX_THIRD_PARTY = 25
    README_CHARS = 500

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def extract(self, files: list[str], graph: dict[str, list[str]]) -> RepoFacts:
        """
        Args:
            files (list[str]): analysed source files (paths relative to the root).
            graph (dict[str, list[str]]): resolved internal dependency graph.

        Returns:
            RepoFacts: the facts sheet plus the vocabulary used for verification.
        """
        file_set = set(files)
        internal_names = self._internal_names(
            files
        )  # Tutti i nomi di ogni singola cartella, incluso il file senza estensione

        file_facts: dict[str, FileFacts] = {}
        identifiers: set[str] = set()
        flags: set[str] = set()

        for rel_path in files:
            facts, ids, file_flags = self._analyze_file(rel_path, internal_names)
            file_facts[rel_path] = facts
            identifiers |= ids
            flags |= file_flags

        restricted = {
            f: [d for d in dict.fromkeys(graph.get(f, [])) if d in file_set and d != f]
            for f in files
        }
        fan_in = dict.fromkeys(files, 0)
        for deps in restricted.values():
            for dep in deps:
                fan_in[dep] += 1
        rank = pagerank(restricted)

        project = self._read_pyproject()
        workflows = self._list_workflows()
        known_paths = self._walk_paths()

        identifiers |= self._project_vocabulary(project, workflows)
        for path in known_paths:
            for part in path.split("/"):
                identifiers.add(part)
                identifiers.add(posixpath.splitext(part)[0])

        sheet = self._render_sheet(
            file_facts, rank, fan_in, project, workflows, flags
        )

        return RepoFacts(
            files=file_facts,
            graph=restricted,
            rank=rank,
            fan_in=fan_in,
            sheet=sheet,
            known_identifiers=frozenset(i for i in identifiers if i),
            known_paths=frozenset(known_paths),
            known_flags=frozenset(flags),
        )

    @staticmethod
    def _internal_names(files: list[str]) -> set[str]:
        names: set[str] = set()
        for path in files:
            for part in path.split("/"):
                names.add(posixpath.splitext(part)[0])
        return names

    def _analyze_file(
        self, rel_path: str, internal_names: set[str]
    ) -> tuple[FileFacts, set[str], set[str]]:
        facts = FileFacts(path=rel_path)
        ids: set[str] = set()
        flags: set[str] = set()

        try:
            with open(
                os.path.join(self.root_dir, rel_path), encoding="utf-8", errors="ignore"
            ) as f:
                tree = ast.parse(f.read(), filename=rel_path)
        except (OSError, SyntaxError, ValueError):
            return facts, ids, flags

        doc = ast.get_docstring(tree) or ""
        facts.docstring = next(
            (line.strip() for line in doc.splitlines() if line.strip()), ""
        )[:140]

        ids, flags = self._collect_identifiers(tree)
        self._collect_import(tree, internal_names, facts)

        self._collect_symbols(tree, facts)

        return facts, ids, flags

    @staticmethod
    def _collect_identifiers(tree: ast.AST) -> tuple[set[str], set[str]]:
        ids: set[str] = set()
        flags: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                ids.add(node.id)
 
            elif isinstance(node, ast.Attribute):
                ids.add(node.attr)

            elif isinstance(node, ast.arg):
                ids.add(node.arg)

            elif isinstance(node, ast.keyword):
                if node.arg:
                    ids.add(node.arg)

            elif isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                ids.add(node.name)

            elif isinstance(node, ast.alias):
                ids.update(node.name.split("."))
                if node.asname:
                    ids.add(node.asname)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    ids.update(node.module.split("."))

            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                value = node.value
                if _FLAG_RE.fullmatch(value):
                    flags.add(value)
                elif _ENV_RE.fullmatch(value):
                    ids.add(value)

        return ids, flags

    def _collect_import(self, tree: ast.AST, internal_names: set[str], facts: FileFacts) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._register_import(alias.name, internal_names, facts)

            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    self._register_import(node.module, internal_names, facts)

    def _collect_symbols(self, tree: ast.Module, facts: FileFacts) -> None:
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods = [
                    m.name
                    for m in node.body
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not m.name.startswith("_")
                ][:_MAX_METHODS_PER_CLASS]
                suffix = f" [{', '.join(methods)}]" if methods else ""
                facts.symbols.append(f"class {node.name}{suffix}")
            elif isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and not node.name.startswith("_"):
                args = [a.arg for a in node.args.args if a.arg not in ("self", "cls")]
                facts.symbols.append(
                    f"def {node.name}({', '.join(args[:_MAX_ARGS_PER_FUNCTION])})"
                )
            elif isinstance(node, ast.If) and self._is_main_guard(node):
                facts.has_main_guard = True
        
        if len(facts.symbols) > _MAX_SYMBOLS_PER_FILE:
            facts.symbols = [*facts.symbols[:_MAX_SYMBOLS_PER_FILE], f"+{len(facts.symbols) - _MAX_SYMBOLS_PER_FILE} more"]

    @staticmethod
    def _register_import(
        module: str, internal_names: set[str], facts: FileFacts
    ) -> None:
        top = module.split(".")[0]
        if (
            top in sys.stdlib_module_names
            or top == "__future__"
            or top in internal_names
        ):
            return
        facts.external_imports.add(top)

    @staticmethod
    def _is_main_guard(node: ast.If) -> bool:
        test = node.test
        return (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
            and any(
                isinstance(c, ast.Constant) and c.value == "__main__"
                for c in test.comparators
            )
        )

    def _read_pyproject(self) -> dict:
        path = os.path.join(self.root_dir, "pyproject.toml")
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            return {}
        return data.get("project", {}) if isinstance(data.get("project"), dict) else {}

    def _list_workflows(self) -> list[str]:
        directory = os.path.join(self.root_dir, ".github", "workflows")
        try:
            names = sorted(
                n for n in os.listdir(directory) if n.endswith((".yml", ".yaml"))
            )
        except OSError:
            return []
        return names

    def _walk_paths(self) -> set[str]:
        paths: set[str] = set()
        count = 0
        for current, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in _WALK_IGNORE]
            rel_dir = os.path.relpath(current, self.root_dir).replace("\\", "/")
            for name in [*dirs, *files]:
                rel = name if rel_dir == "." else f"{rel_dir}/{name}"
                paths.add(rel)
                count += 1
            if count >= _MAX_WALKED_ENTRIES:
                break
        return paths

    @staticmethod
    def _dependency_names(entries: list) -> list[str]:
        names = []
        for entry in entries:
            match = _DEP_NAME_RE.match(str(entry))
            if match:
                names.append(match.group(1))
        return names

    def _project_vocabulary(
        self, project: dict, workflows: list[str]
    ) -> set[str]:
        vocab: set[str] = set()
        name = str(project.get("name", ""))
        if name:
            vocab.add(name)
        for dep in self._dependency_names(project.get("dependencies", [])):
            vocab.add(dep)
        for extra, entries in (project.get("optional-dependencies") or {}).items():
            vocab.add(extra)
            for dep in self._dependency_names(entries):
                vocab.add(dep)
        for script, target in (project.get("scripts") or {}).items():
            vocab.add(script)
            vocab.update(re.split(r"[.:]", str(target)))
        vocab.update(workflows)
        return vocab

    def _read_readme(self) -> str:
        for name in ("README.md", "README.rst", "README.txt", "README"):
            path = os.path.join(self.root_dir, name)
            if not os.path.isfile(path):
                continue
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    lines = f.read(8000).splitlines()
            except OSError:
                return ""
            return self._clean_readme(lines)
        return ""

    def _clean_readme(self, lines: list[str]) -> str:
        collected: list[str] = []
        in_fence = False
        for raw in lines:
            line = raw.strip()
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or not line:
                if collected and sum(map(len, collected)) >= 120 and not line:
                    break
                continue
            if line.startswith(("#", "<", "![", "[![", "|", ">", "---", "===")):
                continue
            line = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", line)
            line = re.sub(r"[*_`]{1,3}", "", line).strip()
            if line:
                collected.append(line)
            if sum(map(len, collected)) >= self.README_CHARS:
                break
        return " ".join(collected)[: self.README_CHARS].strip()

    def _render_sheet(
        self,
        files: dict[str, FileFacts],
        rank: dict[str, float],
        fan_in: dict[str, int],
        project: dict,
        workflows: list[str],
        flags: set[str],
    ) -> str:
        cap = self.MAX_LIST_ITEMS
        lines = [
            "PROJECT FACTS (computed by static analysis of the code; treat as ground truth):"
        ]

        name = project.get("name")
        description = project.get("description")
        if name or description:
            lines.append(
                f"- Project: {name or ''}{' - ' if name and description else ''}{description or ''}"
            )
        readme = self._read_readme()
        if readme:
            lines.append(f"- README extract: {readme}")
        if python_v := project.get("requires-python"):
            lines.append(f"- Requires Python: {python_v}")

        directories = sorted({posixpath.dirname(p) or "." for p in files})
        lines.append(
            f"- Python files analysed: {len(files)}; directories with code: "
            + ", ".join(f"`{d}/`" if d != "." else "`./`" for d in directories[:cap])
            + (f" (+{len(directories) - cap} more)" if len(directories) > cap else "")
        )

        scripts = project.get("scripts") or {}
        if scripts:
            lines.append(
                "- Console scripts: "
                + ", ".join(f"`{k}` -> `{v}`" for k, v in list(scripts.items())[:cap])
            )

        runnable = [p for p, f in files.items() if f.has_main_guard]
        if runnable:
            lines.append(
                "- Run-as-script modules: "
                + ", ".join(f"`{p}`" for p in runnable[:cap])
            )

        roots = [p for p in files if fan_in.get(p, 0) == 0]
        roots.sort(key=lambda p: -rank.get(p, 0.0))
        if roots:
            lines.append(
                "- Modules not imported by any other analysed module (entry or leaf points): "
                + ", ".join(f"`{p}`" for p in roots[:cap])
                + (f" (+{len(roots) - cap} more)" if len(roots) > cap else "")
            )

        central = sorted(files, key=lambda p: (-rank.get(p, 0.0), p))[:cap]
        central = [p for p in central if fan_in.get(p, 0) > 0]
        if central:
            lines.append(
                "- Core modules (most central in the import graph, imported by N modules): "
                + ", ".join(f"`{p}` ({fan_in[p]})" for p in central[:8])
            )

        third_party = sorted(
            {lib for f in files.values() for lib in f.external_imports}
        )
        if third_party:
            lines.append(
                "- Third-party libraries imported by the code: "
                + ", ".join(f"`{x}`" for x in third_party[: self.MAX_THIRD_PARTY])
                + (
                    f" (+{len(third_party) - self.MAX_THIRD_PARTY} more)"
                    if len(third_party) > self.MAX_THIRD_PARTY
                    else ""
                )
            )

        declared = self._dependency_names(project.get("dependencies", []))
        if declared:
            lines.append(
                "- Declared dependencies (pyproject): "
                + ", ".join(f"`{d}`" for d in declared[: self.MAX_THIRD_PARTY])
            )
        extras = list((project.get("optional-dependencies") or {}).keys())
        if extras:
            lines.append(
                "- Optional extras: " + ", ".join(f"`{e}`" for e in extras[:cap])
            )

        if flags:
            lines.append(
                "- CLI-style flags found in code: "
                + ", ".join(f"`{x}`" for x in sorted(flags)[:cap])
            )
        if workflows:
            lines.append(
                "- CI workflows (.github/workflows): "
                + ", ".join(f"`{w}`" for w in workflows[:cap])
            )

        return "\n".join(lines)
