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
`repowhisper/ui_dist/data.json` when `serve_ui()` is used.

## Source paths


```python
engine = RepoWhisper(
    source_target="https://github.com/...",
    llm=llm,
    user_level=UserLevel.JUNIOR,
)
```

`source_target` is an `http://` or `https://` Git repository URL.

Repositories are cloned into a temporary directory and removed during
cleanup after analysis.
