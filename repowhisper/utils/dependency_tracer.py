import os
import ast
from typing import Dict, List, Set

USELESS_FILES: list[str] = [
    "__init__.py"
]

class DependencyTracer:
    """
    Build a dependencies graph using the Abstract Syntax Tree (AST).
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def build_graph(self) -> Dict[str, List[str]]:
        graph = {}
        ignore_dirs = {'tests', 'test', '__tests__', 'venv', '.venv', 'node_modules', '.git'}
        
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                if file.endswith('.py') and file not in USELESS_FILES:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.root_dir).replace("\\", "/")
                    graph[rel_path] = self._extract_python_dependencies(file_path)

        resolved_graph = {}
        valid_files = list(graph.keys())
        
        for file, deps in graph.items():
            resolved_deps = []
            for dep in deps:
                resolved_file = self._resolve_module_to_file(dep, valid_files)
                if resolved_file:
                    resolved_deps.append(resolved_file)
            resolved_graph[file] = resolved_deps

        print(resolved_graph)
            
        return resolved_graph

    def _extract_python_dependencies(self, file_path: str) -> List[str]:
        """
        Legge il codice sfruttando la comprensione grammaticale di Python (AST), 
        ignorando stringhe, commenti e rumore di fondo.
        """
        deps = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=file_path)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        deps.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        deps.append(node.module)
        except Exception:
            pass
        return deps

    def _resolve_module_to_file(self, module_name: str, valid_files: List[str]) -> str | None:
        """
        Converte un namespace (es. 'utils.console') nel file reale ('utils/console.py').
        """
        path_suffix = module_name.replace('.', '/')
        possible_matches = [
            f"{path_suffix}.py",
        ]
        
        for valid_file in valid_files:
            for match in possible_matches:
                # Controlliamo se il file fisico nel progetto termina con il pattern richiesto
                if valid_file.endswith(match):
                    return valid_file
        return None

    def get_ordered_processing_list(self, graph: Dict[str, List[str]]) -> List[str]:
        """
        Esegue la Depth-First Search (DFS) per garantire che i file 
        privi di dipendenze vengano elaborati per primi dall'Intelligenza Artificiale.
        """
        visited: Set[str] = set()
        ordered_list: List[str] = []

        def dfs(node: str):
            if node in visited:
                return
            visited.add(node)
            for dependency in graph.get(node, []):
                if dependency not in visited:
                    dfs(dependency)
            ordered_list.append(node)

        for file_node in graph:
            dfs(file_node)

        return ordered_list