# Ingestion and Search

## Source ingestion

[Ingestor](api.md) uses language-aware LangChain loaders and
splitters. Python is currently registered in `LANGUAGE_MAP` with the `.py`
extension.

The default process is:

1. discover files with the configured extension;
2. parse source using `LanguageParser`;
3. split documents with a Python-aware text splitter;
4. return LangChain `Document` objects.

Unsupported language names are ignored with a warning.

## Embeddings and Chroma

[ChromaDBManager](api.md) creates embeddings with
`all-MiniLM-L6-v2` and persists the resulting collection in `./db`.

The manager exposes semantic retrieval through:

```python
results = memory_manager.search_code("authentication flow", top_k=3)
```

The current workflow builds the vector store as part of initialization but the
agent workflow primarily reads files directly in the Navigator phase.

## Dependency graph

[DependencyTracer](api.md) walks the repository, parses
Python imports with the AST, resolves imports to repository files, and produces
a dependency graph. A depth-first traversal generates the file processing
order. Circular dependencies are detected and reported instead of recursing
indefinitely.
