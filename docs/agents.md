# Agents and Workflow

The workflow is implemented by
[AgentsWorkflow](api.md) using LangGraph.

## Architect

The Architect receives the generated directory tree and produces an executive
architectural summary. It should describe only evidence present in the tree.

## Navigator

The Navigator receives one source file at a time. Its structured output
contains:

- a prose explanation;
- selected line-level notes;
- one-based line numbers in its model response.

The workflow converts those line numbers to zero-based indexes for the final
JSON consumed by the frontend.

## Reviewer

The Reviewer evaluates whether an explanation describes the code accurately
without attempting to debug it or propose unrelated fixes. A rejected
explanation is sent back to the Navigator with feedback.

## Storyteller

The Storyteller combines the architecture summary and accepted module
explanations into the final narrative and JSON payload.

## Retry behavior

The Navigator and Reviewer form a feedback loop:

```text
Navigator -> Reviewer -> approved -> next file
                 |
                 +---- rejected -> Navigator
```

The workflow continues until all files in the dependency order have been
processed, then invokes the Storyteller.
