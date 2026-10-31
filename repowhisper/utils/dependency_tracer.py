import os
import re

#TODO use import patterns based on the actual languages the user wants explanations about
LANGUAGES_IMPORT_PATERNS: dict[str, list[str]] = {
    "python": [r'^import\s+([\w\.]+)', r'^from\s+([\w\.]+)\s+import'],
    "javascript": [r'import\s+.*from\s+[\'"]([^\'"]+)[\'"]',r'require\([\'"]([^\'"]+)[\'"]\)']
}

class DependencyTracer:
    """
    Analyzes source code files to build a dependency graph and determines 
    the optimal chronological order for AI analysis using topological sorting.
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

        self.import_patterns = [
            re.compile(path) for imports in LANGUAGES_IMPORT_PATERNS.values() for path in imports   
        ]

    def build_graph(self) -> dict[str, list[str]]:
        """
        Scans all valid source files and maps which files depend on which modules.
        
        Returns:
            Dict[str, List[str]]: A dictionary where keys are file paths and 
                                  values are lists of imported module names.
        """
        graph = {}
        for root, _ , files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(('.py', '.js', '.ts')):
                    file_path = os.path.join(root,file)
                    rel_path = os.path.relpath(file_path, self.root_dir)
                    graph[rel_path] = self._extract_dependencies(file_path)
        return graph

    def _extract_dependencies(self, file_path: str) -> list[str]:
        """Reads a file and uses regex to find all import statements."""
        deps = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    for pattern in self.import_patterns:
                        match = pattern.search(line.strip())
                        if match:
                            deps.append(match.group(1))
        except UnicodeDecodeError:
            pass
        return deps

    def get_ordered_processing_list(self, graph: dict[str, list[str]]) -> list[str]:
        """
        Performs a Topological Sort to determine the order of execution.
        Files with zero internal dependencies (leaf nodes) are processed first.
        """
        visited: set[str] = set()
        ordered_list: list[str] = []

        def dfs(node:str):
            if node in visited:
                return

            visited.add(node)

            for internal_file in graph:
                if (node.replace('.', '/') in internal_file or node in internal_file) and internal_file not in visited:
                        dfs(internal_file)

            ordered_list.append(node)

        for file_node in graph:
            dfs(file_node)

        local_ordered_files = [
            f for f in ordered_list if f in graph.keys()
        ]

        return local_ordered_files