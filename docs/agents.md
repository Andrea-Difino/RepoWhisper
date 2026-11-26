# Agents and Workflow

The workflow is implemented by
[AgentsWorkflow](api.md) using LangGraph.

## Architect

The Architect runs after the per-file analysis. It receives a budgeted directory
tree, a facts sheet computed by static analysis, and short per-module notes, and
produces an executive architectural summary. It must mention only names that appear
in that evidence, written in `backticks` so they can be verified.

## Navigator

The Navigator receives one source file at a time. Its structured output
contains:

- a prose explanation;
- a one-line summary (`one_liner`, optional: the first sentence of the explanation
  is used when a model omits it);
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

The Storyteller combines the facts sheet, the module notes and the Architect draft
into the final narrative and JSON payload. When facts and draft disagree, the facts
win.

## Package summarizer

A small helper agent used only when the module notes do not fit `context_budget`.
It compresses the notes of one directory into at most three factual sentences and
never sees raw source code.

## Grounding verifier

Not an agent: a deterministic check (no tokens). It extracts every `code reference`
from the generated text and verifies it against the names found in the repository
(files, classes, functions, arguments, libraries, flags, environment variables). It
catches invented names, not incorrect descriptions of behaviour.

## Retry behavior

The Navigator and Laya Reviewer form a feedback loop:

```text
Navigator -> Reviewer -> approved -> next file
                 |
                 +---- rejected -> Navigator
```

The workflow continues until all files in the dependency order have been
processed, then builds the facts and invokes the Architect and the Storyteller.
