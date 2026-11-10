import os

from .tracers.base_tracer import BaseLanguageTracer
from .tracers.python_tracer import PythonTracer


class DependencyTracer:
    """
    Build a dependencies graph module. Language agnostic
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

        self._tracers: dict[str, BaseLanguageTracer] = {}
        self._register_tracer(PythonTracer())

    def _register_tracer(self, tracer: BaseLanguageTracer):
        """Register a tracer with its extension"""
        self._tracers[tracer.extension] = tracer

    def build_graph(self) -> dict[str, list[str]]:
        graph = {}
        ignore_dirs = {'tests', 'test', '__tests__', 'venv', '.venv', 'node_modules', '.git'}

        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                _, ext = os.path.splitext(file)

                if ext in self._tracers:
                    tracer = self._tracers[ext]

                    if not tracer.is_useless(file):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.root_dir).replace("\\", "/")

                        graph[rel_path] = tracer.extract_dependencies(file_path, self.root_dir)

        resolved_graph = {}
        valid_files = list(graph.keys())

        indices = {}
        for ext, tracer in self._tracers.items():
            lang_files = [f for f in valid_files if f.endswith(ext)]
            indices[ext] = tracer.build_module_index(lang_files)

        for file, deps in graph.items():
            _, ext = os.path.splitext(file)
            tracer = self._tracers[ext]
            tracer_index = indices.get(ext, {})

            resolved_deps = []
            for dep in deps:
                resolved_file = tracer.resolve_module_to_file(dep, tracer_index)
                if resolved_file:
                    resolved_deps.append(resolved_file)

            resolved_graph[file] = resolved_deps
            
        return resolved_graph

    def get_ordered_processing_list(self, graph: dict[str, list[str]]) -> list[str]:
        """
        Advanced DFS with states WHITE (0), GRAY (1), BLACK (2) 
        to safely detect circular dependencies.
        """
        visited = {}  # 0: WHITE, 1: GRAY, 2: BLACK
        ordered_list = []

        def dfs(node: str):
            state = visited.get(node, 0)
            if state == 1:
                print(f"Detected circular dependency on module: {node}")
                return
            if state == 2:
                return

            visited[node] = 1

            for dependency in graph.get(node, []):
                if dependency in graph:
                    dfs(dependency)

            visited[node] = 2
            ordered_list.append(node)

        for file_node in graph:
            if visited.get(file_node, 0) == 0:
                dfs(file_node)

        return ordered_list