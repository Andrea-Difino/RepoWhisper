# Source Analysis

The analysis workflow reads source files directly during the Navigator phase.
The dependency tracer determines the processing order and the Navigator sends
each selected file to the configured language model for explanation.

## Dependency graph

[DependencyTracer](api.md) walks the repository, parses
Python imports with the AST, resolves imports to repository files, and produces
a dependency graph. A depth-first traversal generates the file processing
order. Circular dependencies are detected and reported instead of recursing
indefinitely.
