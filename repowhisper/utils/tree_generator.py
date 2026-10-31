import os
from typing import ClassVar


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
    def generate(dir_path: str, prefix: str = "", ignore_dirs: set[str] | None = None) -> str:
        """
        Recursively builds a tree-like string of the directory.
        
        Args:
            dir_path (str): The root directory to scan.
            prefix (str): Used internally for formatting the tree branches.
            ignore_dirs (set[str] | None): Directories to skip.
            
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
                extension = "    " if index == count - 1 else "│   "
                tree_str += ProjectTreeGenerator.generate(
                    path, prefix=prefix + extension, ignore_dirs=ignore_dirs
                )
                
        return tree_str