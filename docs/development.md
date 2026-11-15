# Development

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The tests are under `tests/unit/` and cover agents, the facade, memory,
ingestion, utilities, and workflow behavior.

## Build documentation

```powershell
.\.venv\Scripts\mkdocs.exe build --strict
```

Preview changes while editing:

```powershell
.\.venv\Scripts\mkdocs.exe serve
```

The generated `site/` directory is ignored by Git.

## Add a supported language

To add another source language:

1. register its extension and splitter language in
   [ingestor.py](https://github.com/Andrea-Difino/RepoWhisper/blob/main/repowhisper/ingestion/ingestor.py);
2. implement a language-specific tracer derived from
   [BaseLanguageTracer](api.md);
3. register the tracer in `DependencyTracer`;
4. add focused tests;
5. document the language and its limitations.

## Add an agent

New agents should implement the `BaseAgent.analyze()` contract, receive the
LLM through dependency injection, and be wired into `AgentsWorkflow` with an
explicit state contract.

Avoid putting provider-specific configuration inside agents. The facade should
continue accepting any compatible LangChain chat model.
