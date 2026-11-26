# Web Interface

`RepoWhisper.analyze()` serves the bundled frontend locally.

```python
engine.analyze()
```

The method:

1. runs the analysis when JSON data path is not supplied;
2. serves the report at `/data.json` without modifying the bundled UI files;
3. starts an HTTP server bound to the local machine;
4. opens the default browser.

The default address is:

```text
http://127.0.0.1:8543
```

Use a custom port with:

```python
engine.analyze(port=9000)
```

You can also load an existing `data.json` file by passing its path.
`analyze()` validates and serializes the report before serving it to the UI:

```python
engine.analyze(json_path="data.json")
```

The server runs until interrupted with `Ctrl+C` and only accepts connections
from the local machine.

In an application entry point, handle failures around `analyze()`:

```python
try:
    engine.analyze()
except RepoWhisperError as e:
    print(f"RepoWhisperError failed: {e}")
```

User interruptions are handled by RepoWhisper. Other errors, such as provider,
repository, or server failures, are propagated to the caller.

## Frontend data contract

The frontend expects the schema described in [Output Format](output.md).
`raw_modules` provides source code and explanations, while `notes` supplies
line-level annotations for the code viewer.

## Operational notes

- The report served at `/data.json` contains source code from the analyzed
  repository.
- The server is bound to loopback and is not exposed to other devices on the
  network.
- Stop the server with `Ctrl+C`.
