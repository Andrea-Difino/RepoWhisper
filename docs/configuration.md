# Configuration

## LLM configuration

The facade accepts any LangChain `BaseChatModel`, so provider configuration is
kept outside RepoWhisper:

```python
import os

from langchain_groq import ChatGroq

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

## Local storage

The vector store is created in `./db` by
[ChromaDBManager](api.md). The default embedding model
is `all-MiniLM-L6-v2`; the first run may download model files.

The generated frontend data is written to
`repowhisper/ui_dist/data.json` when `serve_ui()` is used.

## Source paths

`source_target` can be:

- an existing local directory;
- an `http://` or `https://` Git repository URL.

Remote repositories are cloned into a temporary directory and removed during
cleanup after analysis.
