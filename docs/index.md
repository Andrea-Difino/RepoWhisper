# RepoWhisper

RepoWhisper analyzes a software repository and generates navigable technical
documentation with a multi-agent workflow.

## What it does

RepoWhisper accepts a local directory or a Git repository URL, inspects its
structure and dependencies, reads the supported source files, and produces:

- an architectural summary;
- a file-by-file explanation;
- targeted line-level notes;
- a JSON document consumed by the bundled web interface.

The public entry point is the [`RepoWhisper`](api.md) facade.

## Documentation map

- [Installation](installation.md) - install the project and documentation tools.
- [Quick Start](quickstart.md) - run a complete analysis.
- [Configuration](configuration.md) - configure the LLM provider and analysis level.
- [System Overview](architecture.md) - understand the end-to-end pipeline.
- [Output Format](output.md) - consume the generated JSON.
- [API Reference](api.md) - inspect the Python API.

## Current scope

The ingestion pipeline currently supports Python source files. The dependency
tracer is designed around language-specific tracer implementations, so other
languages can be added without changing the public facade.
