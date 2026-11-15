# Installation

## Requirements

- Python 3.12.
- Git, when analyzing a remote repository.
- An LLM provider supported by LangChain.
- Enough disk space for the local embedding model and Chroma database.

## Install the project

From the repository root:

```powershell
uv sync
```

Or install the package with pip:

```powershell
python -m pip install .
```

Optional LLM integrations are declared in `pyproject.toml`:

```powershell
python -m pip install "RepoWhisper[groq]"
python -m pip install "RepoWhisper[ollama]"
python -m pip install "RepoWhisper[openai]"
python -m pip install "RepoWhisper[anthropic]"
```

## Install documentation dependencies

The development dependency group includes MkDocs and mkdocstrings:

```powershell
uv sync --group dev
```

Build the documentation with:

```powershell
.\.venv\Scripts\mkdocs.exe build --strict
```

Preview it locally with:

```powershell
.\.venv\Scripts\mkdocs.exe serve
```

## Credentials

Do not commit credentials. Store provider keys in environment variables or a
local `.env` file, which is ignored by Git.
