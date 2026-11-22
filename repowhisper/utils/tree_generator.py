import os
from typing import ClassVar

from utils.token_budget import TokenUtilities


class ProjectTreeGenerator:
    """
    Generates a textual representation of the project's directory structure.
    Ignores common build, virtual environment, and hidden directories to 
    save LLM context window tokens.
    """
    
    DEFAULT_IGNORE: ClassVar[set[str]] = {
        ".git", "__pycache__", "node_modules", "venv", ".venv", 
        ".idea", ".vscode", "dist", "build",
        "tests", "test", "__tests__"
    }

    @staticmethod
    def generate(
        dir_path: str,
        prefix: str = "",
        ignore_dirs: set[str] | None = None,
        max_depth: int | None = None,
        _depth: int = 1,
    ) -> str:
        """
        Recursively builds a tree-like string of the directory.
        
        Args:
            dir_path (str): The root directory to scan.
            prefix (str): Used internally for formatting the tree branches.
            ignore_dirs (set[str] | None): Directories to skip.
            max_depth (int | None): If set, directories nested deeper than this are not
                expanded and are shown with an item count instead.
            _depth (int): Used internally to track the current depth.
            
        Returns:
            str: The visual tree representation of the folder structure.
        """
        if ignore_dirs is None:
            ignore_dirs = ProjectTreeGenerator.DEFAULT_IGNORE
            
        tree_str = ""
        try:
            items = os.listdir(dir_path)
            items.sort(key=lambda x: (not os.path.isdir(os.path.join(dir_path, x)), x))
        except PermissionError:
            return tree_str

        count = len(items)
        for index, item in enumerate(items):
            if item in ignore_dirs:
                continue
                
            path = os.path.join(dir_path, item)
            connector = "└── " if index == count - 1 else "├── "
            tree_str += f"{prefix}{connector}{item}\n"
            
            if os.path.isdir(path):
                if max_depth is not None and _depth >= max_depth:
                    hidden = ProjectTreeGenerator._count_visible(path, ignore_dirs)
                    if hidden:
                        extension = "    " if index == count - 1 else "│   "
                        tree_str += f"{prefix}{extension}└── … ({hidden} items not expanded)\n"
                    continue

                extension = "    " if index == count - 1 else "│   "
                tree_str += ProjectTreeGenerator.generate(
                    path,
                    prefix=prefix + extension,
                    ignore_dirs=ignore_dirs,
                    max_depth=max_depth,
                    _depth=_depth + 1,
                )
                
        return tree_str

    @staticmethod
    def _count_visible(dir_path: str, ignore_dirs: set[str]) -> int:
        try:
            return sum(1 for item in os.listdir(dir_path) if item not in ignore_dirs)
        except OSError:
            return 0

    @staticmethod
    def generate_within_budget(dir_path: str, max_tokens: int) -> str:
        """
        Builds the deepest tree that fits in `max_tokens`.

        The full tree is returned when it fits. Otherwise the tree is generated with a
        decreasing maximum depth, so every top-level area stays visible and only the
        deepest levels are collapsed into item counts.

        Args:
            dir_path (str): The root directory to scan.
            max_tokens (int): Token budget for the tree.

        Returns:
            str: A tree whose estimated size is within the budget (depth 1 is the floor).
        """
        full = ProjectTreeGenerator.generate(dir_path)
        if TokenUtilities.estimate_tokens(full) <= max_tokens:
            return full

        tree = full
        for depth in range(8, 0, -1):
            tree = ProjectTreeGenerator.generate(dir_path, max_depth=depth)
            if TokenUtilities.estimate_tokens(tree) <= max_tokens:
                return tree
        return tree