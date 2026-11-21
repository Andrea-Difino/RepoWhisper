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

## Laya Reviewer

The Reviewer is a locally calibrated Laya/Vega classifier, not an LLM agent.
It predicts whether a Navigator draft is an `EXPLANATION` or a debugging-oriented
`DEBUG`. A `DEBUG` result returns corrective feedback and sends the draft back
to the Navigator. This review step runs locally and consumes no LLM tokens.

## Storyteller

The Storyteller combines the architecture summary and accepted module
explanations into the final narrative and JSON payload.

## Retry behavior

The Navigator and Laya Reviewer form a feedback loop:

```text
Navigator -> Reviewer -> approved -> next file
                 |
                 +---- rejected -> Navigator
```

The workflow continues until all files in the dependency order have been
processed, then invokes the Storyteller.
