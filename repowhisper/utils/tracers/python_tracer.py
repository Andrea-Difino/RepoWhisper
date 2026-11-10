import ast
import os

from base_tracer import BaseLanguageTracer


class PythonTracer(BaseLanguageTracer):
    """
    Specific implementation for python, based on AST
    """
    
    @property
    def extension(self) -> str:
        return '.py'

    def is_useless(self, filename: str) -> bool:
        return False

    def extract_dependencies(self, file_path: str, root_dir: str) -> list[str]:
        deps = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            tree = ast.parse(code_content, filename=file_path)

            rel_path = os.path.relpath(file_path, root_dir)
            mod_parts = os.path.splitext(rel_path)[0].replace("\\", "/").split("/")
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        deps.append(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    if node.level > 0:
                        target_parts = mod_parts[:-node.level]
                        if node.module:
                            target_parts.extend(node.module.split("."))
                        deps.append(node.module)
                    elif node.module:
                        deps.append(node.module)
        except (OSError, SyntaxError) as exc:
            print(f"Impossible to analyze {file_path}: {exc}")
        return deps

    def build_module_index(self, valid_files: list[str]) -> dict[str, str]:

        index = {}
        for file_path in valid_files:
            clean_path = os.path.splitext(file_path)[0]
            parts = clean_path.replace("\\", "/").split("/")

            for i in range(len(parts)):
                module_name = ".".join(parts[i:])
                index[module_name] = file_path

            if os.path.basename(file_path) == "__init__.py":
                dir_parts = parts[:-1]
                if dir_parts:
                    dir_module_name = ".".join(dir_parts)
                    index[dir_module_name] = file_path

        return index


    def resolve_module_to_file(self, module_name: str, module_index: dict[str, str]) -> str | None:
        
        if module_name in module_index:
            return module_index[module_name]
            
        for key, _ in module_index:
            if module_name.endswith(key) or key.endswith(module_name):
                return module_index[key]
                
        return None