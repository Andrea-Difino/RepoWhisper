import ast

from base_tracer import BaseLanguageTracer


class PythonTracer(BaseLanguageTracer):
    """
    Specific implementation for python, based on AST
    """
    
    @property
    def extension(self) -> str:
        return '.py'

    def is_useless(self, filename: str) -> bool:
        return filename in ["__init__.py"]

    def extract_dependencies(self, file_path: str) -> list[str]:
        deps = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=file_path)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        deps.append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    deps.append(node.module)
        except (OSError, SyntaxError) as exc:
            print(f"Impossible to analyze {file_path}: {exc}")
        return deps

    def resolve_module_to_file(self, module_name: str, valid_files: list[str]) -> str | None:
        path_suffix = module_name.replace('.', '/')
        possible_matches = [f"{path_suffix}.py"]
        
        for valid_file in valid_files:
            for match in possible_matches:
                if valid_file.endswith(match):
                    return valid_file
        return None