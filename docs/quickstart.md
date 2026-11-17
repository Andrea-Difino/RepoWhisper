# Quick Start

The facade accepts a source target, an initialized LangChain chat model, and an
optional explanation level.

```python
from langchain_groq import ChatGroq
from repowhisper import RepoWhisper, UserLevel

llm = ChatGroq(
    api_key="read this from an environment variable",
    model="openai/gpt-oss-120b",
    max_tokens=6000,
)

engine = RepoWhisper(
    source_target="repo_url",
    llm=llm,
    user_level=UserLevel.JUNIOR,
)

try:
    json_data = engine.generate_documentation()
except Exception as exc:
    print(f"RepoWhisper failed: {exc}")
```

`generate_documentation()` returns a JSON string when analysis succeeds and
`None` when the run is interrupted or cannot produce a result.

The `try/except` is recommended because provider, repository, and processing
errors are propagated to the caller.

To generate the documentation and open the bundled interface in a browser:

```python
engine.serve_ui()
```

For an application entry point, wrap the call in `try/except` to handle
provider, repository, and server errors without an unhandled traceback:

```python
try:
    engine.serve_ui()
except Exception as exc:
    print(f"RepoWhisper failed: {exc}")
```

`RepoWhisper` handles user interruptions internally. Other errors are raised
to the caller so that applications can log them or present an appropriate
message.

The default server port is `8543`. Pass a different port when needed:

```python
engine.serve_ui(port=9000)
```

For a complete runnable example, see
[repowhisper/main.py](https://github.com/Andrea-Difino/RepoWhisper/blob/main/repowhisper/main.py).

## Explanation levels

`UserLevel` changes the amount and style of explanation produced by the
Navigator and Storyteller agents:

- `UserLevel.JUNIOR` provides detailed, educational explanations.
- `UserLevel.MID` focuses on integration, contracts, and state transitions.
- `UserLevel.SENIOR` emphasizes trade-offs, performance, and extension points.
