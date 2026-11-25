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

::: utils.exceptions


## Internal components

The following sections expose implementation contracts for contributors.


### Source management

::: ingestion.source_manager

### JSON validation

::: schemas.analysis_schema

### Agents

::: agents.base_agent

::: agents.architect

::: agents.navigator

::: agents.reviewer

::: agents.storyteller

### Orchestration

::: orchestration.state

::: orchestration.workflow

### Analysis

::: analysis.dependency_tracer

::: analysis.tree_generator

::: analysis.facts_extractor

### Grounding

::: utils.evidence_packer

::: utils.grounding_verifier

### Utilities

::: utils.token_budget

::: utils.tracers.base_tracer

::: utils.tracers.python_tracer
