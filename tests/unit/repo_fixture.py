"""Shared helpers: builds a tiny but realistic Python repository on disk."""
import textwrap

from repowhisper.utils.dependency_tracer import DependencyTracer


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


def make_repo(root):
    write(root / "pyproject.toml", """
        [project]
        name = "demo-app"
        description = "Demo application that cleans data."
        requires-python = ">=3.12"
        dependencies = ["requests>=2.0", "langchain-core>=1.0"]
        [project.optional-dependencies]
        extra = ["rich>=13"]
        [project.scripts]
        demo = "app.cli:main"
    """)
    write(root / "README.md", """
        # Demo

        [![badge](https://example.com/b.svg)](https://example.com)

        **Demo** cleans and validates tabular data before loading it.

        ## Install
        pip install demo
    """)
    write(root / ".github" / "workflows" / "ci.yaml", "name: CI\non: push\n")
    write(root / "app" / "__init__.py", "")
    write(root / "app" / "core.py", '''
        """Core cleaning engine."""


        class Engine:
            def run(self, data, strict=False):
                return helper(data)

            def _private(self):
                return None


        def helper(data, mode="fast"):
            return data
    ''')
    write(root / "app" / "util.py", '''
        """Small utilities."""
        from app.core import helper


        def shout(text):
            return helper(text).upper()
    ''')
    write(root / "app" / "cli.py", '''
        """Command line entry point."""
        import argparse
        import os

        import requests

        from app.core import Engine
        from app.util import shout


        def main():
            parser = argparse.ArgumentParser()
            parser.add_argument("--dry-run", action="store_true")
            token = os.environ["DEMO_TOKEN"]
            Engine().run(shout("x"))
            requests.get("https://example.com", headers={"auth": token})


        if __name__ == "__main__":
            main()
    ''')


def analysed_files(root):
    tracer = DependencyTracer(str(root))
    graph = tracer.build_graph()
    files = [f for f in tracer.get_ordered_processing_list(graph) if not f.endswith("__init__.py")]
    return files, graph
