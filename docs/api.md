# API Reference

## Public facade

::: repowhisper

## UserLevel

The available levels are:

- `UserLevel.JUNIOR`: detailed explanations.
- `UserLevel.MID`: medium-depth explanations.
- `UserLevel.SENIOR`: concise explanations.

## Custom Exceptions

Below are listed all the custom exceptions that the user can encounter during the use of the library.
  
### Exceptions

::: repowhisper.utils.exceptions


## Internal components

The following sections expose implementation contracts for contributors.


### Source management

::: repowhisper.ingestion.source_manager

### JSON validation

::: repowhisper.schemas.analysis_schema

### Agents

::: repowhisper.agents.base_agent

::: repowhisper.agents.architect

::: repowhisper.agents.navigator

::: repowhisper.agents.reviewer

::: repowhisper.agents.storyteller

### Orchestration

::: repowhisper.orchestration.state

::: repowhisper.orchestration.workflow

### Analysis

::: repowhisper.analysis.dependency_tracer

::: repowhisper.analysis.tree_generator

::: repowhisper.analysis.facts_extractor

### Grounding

::: repowhisper.grounding.evidence_packer

::: repowhisper.grounding.grounding_verifier

### Utilities

::: repowhisper.utils.token_budget

::: repowhisper.analysis.tracers.base_tracer

::: repowhisper.analysis.tracers.python_tracer
