# RepoWhisper

RepoWhisper analyzes a software repository and generates navigable technical
documentation with a multi-agent workflow.

> **Python scope:** RepoWhisper is currently a Python code-analysis library.
> Python source files and Python import graphs are supported. It does not yet
> provide equivalent analysis for JavaScript, TypeScript, Java, Go, Rust, or
> other languages.

## What it does

RepoWhisper accepts a public GitHub repository URL, inspects its Python
structure and dependencies, reads supported Python source files, and produces:

- an architectural summary;
- a file-by-file explanation;
- targeted line-level notes;
- a JSON document consumed by the bundled web interface.

Architectural explanations and narration are produced by the configured
LangChain model. Module-draft review is handled separately by the local,
calibrated Laya/Vega Reviewer.

The public entry point is the [`RepoWhisper`](api.md) facade.

## Documentation map

- [Installation](installation.md) - install the project and documentation tools.
- [Quick Start](quickstart.md) - run a complete analysis.
- [Configuration](configuration.md) - configure the LLM provider and analysis level.
- [System Overview](architecture.md) - understand the end-to-end pipeline.
- [Output Format](output.md) - consume the generated JSON.
- [API Reference](api.md) - inspect the Python API.

## Current scope

The dependency tracer currently analyzes Python imports. Its tracer structure
allows additional languages to be added without changing the public facade.
