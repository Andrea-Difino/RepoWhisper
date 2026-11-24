# Development

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The tests are under `tests/unit/` and cover agents, the facade, source
management, utilities, and workflow behavior.

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

RepoWhisper is currently Python-only. Adding another source language requires
coordinated changes rather than a tracer-only extension:

1. implement a language-specific tracer derived from
   [BaseLanguageTracer](api.md);
2. register the tracer in `DependencyTracer`;
3. add language-specific static facts extraction and grounding vocabulary;
4. teach the tree and source-selection rules about the new file types;
5. add focused tests for parsing, ordering, facts, and grounding;
6. document the language and its limitations.

## Add an agent

New agents should implement the `BaseAgent.analyze()` contract, receive the
LLM through dependency injection, and be wired into `AgentsWorkflow` with an
explicit state contract.

Avoid putting provider-specific configuration inside agents. The facade should
continue accepting any compatible LangChain chat model.
