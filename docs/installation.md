# Installation

## Requirements

- Python 3.12.
- Git, when analyzing a remote repository.
- An LLM provider supported by LangChain.

## Install from PyPI

For the standard installation, install the published package from PyPI:

```powershell
python -m pip install repowhisper
```

The base package includes RepoWhisper and its core dependencies. To install
RepoWhisper together with the integration for a specific LLM provider, use
the corresponding optional dependency:

```powershell
python -m pip install "repowhisper[groq]"
python -m pip install "repowhisper[ollama]"
python -m pip install "repowhisper[openai]"
python -m pip install "repowhisper[anthropic]"
```

Each provider extra includes the base RepoWhisper installation and the
provider-specific LangChain integration.

## Install from the repository

For development, or to work with the source code, clone the repository and
install the project from its root:

```powershell
uv sync
```

Alternatively, install the local package with pip:

```powershell
python -m pip install .
```

Optional LLM integrations can also be installed from the local checkout:

```powershell
python -m pip install ".[groq]"
python -m pip install ".[ollama]"
python -m pip install ".[openai]"
python -m pip install ".[anthropic]"
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
