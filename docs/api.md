# API Reference

## Public facade

::: repowhisper

## UserLevel

The available levels are:

- `UserLevel.JUNIOR`: detailed explanations.
- `UserLevel.MID`: medium-depth explanations.
- `UserLevel.SENIOR`: concise explanations.

## Internal components

The following sections expose implementation contracts for contributors.

### Ingestion

::: ingestion.ingestor

::: ingestion.source_manager

### Agents

::: agents.base_agent

::: agents.architect

::: agents.navigator

::: agents.reviewer

::: agents.storyteller

### Orchestration

::: orchestration.state

::: orchestration.workflow

### Memory

::: memory.chroma_db_manager

### Utilities

::: utils.dependency_tracer

::: utils.tree_generator

::: utils.tracers.base_tracer

::: utils.tracers.python_tracer
