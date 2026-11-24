# System Overview

RepoWhisper is organized as a facade, source management layer, agent layer,
and orchestration layer.

## Execution phases

1. `SourceManager` clones a GitHub HTTP(S) repository URL into a temporary local
   directory.
2. `DependencyTracer` builds a dependency graph and processing order.
3. `CodeNavigator` explains each file and returns line-level notes plus a one-line
   summary. It also receives the one-line summaries of the already analysed modules
   that the file imports.
4. The local `LayaReviewer` classifies the draft as `EXPLANATION` or `DEBUG`; a
   `DEBUG` draft is sent back to the Navigator.
5. `FactsExtractor` (no LLM) computes verifiable facts from the code: symbols,
   third-party imports, entry points, import graph, PageRank, `pyproject.toml`
   metadata, README excerpt and CI workflows. `EvidencePacker` packs the per-file
   notes into the configured token budget.
6. `Architect` writes the architectural overview from that grounded evidence
   (not from the bare directory tree).
7. `Storyteller` combines the facts, the module notes and the architect draft.
8. `GroundingVerifier` (no LLM) checks every `code reference` in the Architect and
   Storyteller output against the repository. If invented names are found, the
   agent is asked to regenerate once.
9. The final state is serialized to the documented JSON format.

## Grounding and token budget

The evidence handed to the Architect and the Storyteller is limited by
`context_budget` (estimated tokens, default `6000`), so every call has a bounded
size regardless of the repository size.

- If the per-file notes fit the budget, no extra LLM call is made.
- Otherwise the notes are collapsed directory by directory, least central first,
  using the small `PackageSummarizer` agent (one bounded call per directory).
  If it fails, a deterministic summary is used.
- Important modules are placed at the start and at the end of the prompt.

The state contract is defined in
[orchestration/state.py](https://github.com/Andrea-Difino/RepoWhisper/blob/main/repowhisper/orchestration/state.py).
