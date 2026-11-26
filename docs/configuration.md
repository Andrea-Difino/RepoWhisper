# Configuration

## LLM configuration

The facade accepts any LangChain `BaseChatModel`, so provider configuration is
kept outside RepoWhisper:

```python
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    api_key=os.environ["GROQ_API_KEY"],
    model="openai/gpt-oss-120b",
    max_tokens=6000,
)
```

The example application loads environment variables with `python-dotenv`.
Use the provider's LangChain integration and pass the resulting model to
`RepoWhisper`.

## Optional integrations

Provider integrations are optional dependencies. Install only the one needed
by the application:

- `RepoWhisper[groq]`
- `RepoWhisper[ollama]`
- `RepoWhisper[openai]`
- `RepoWhisper[anthropic]`

The generated frontend data is written to
`repowhisper/ui_dist/data.json` when `analyze()` is used.

## Context budget

```python
engine = RepoWhisper(source_target, llm, UserLevel.MID, context_budget=4000)
```

`context_budget` (default `6000`) is the maximum estimated number of tokens of
evidence given to the Architect and the Storyteller. Lower it for models with a
small context window or strict per-minute token limits: the per-file notes are
compressed to fit. The model still needs room for its own instructions and output on
top of the budget. Token counts are estimated (about 3.5 characters per token), so
they are intentionally conservative rather than tokenizer-exact.

## Laya Reviewer

The Reviewer is local and is not configured through LangChain. On first use,
RepoWhisper downloads and caches the Vega reader, its backbone model, and the
RepoWhisper calibration files. The review step requires no provider API key and
does not consume tokens.

## Source paths


```python
engine = RepoWhisper(
    source_target="https://github.com/...",
    llm=llm,
    user_level=UserLevel.JUNIOR,
)
```

`source_target` is an `http://github.com/` or `https://github.com/` repository
URL. The source manager does not accept local filesystem paths.

Repositories are cloned into a temporary directory and removed during
cleanup after analysis.
