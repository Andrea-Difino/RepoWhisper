# Web Interface

`RepoWhisper.analyze()` serves the bundled frontend locally.

```python
engine.analyze()
```

The method:

1. runs the analysis when JSON data path is not supplied;
2. writes the JSON to `repowhisper/ui_dist/data.json`;
3. writes the report into the bundled UI data file;
4. starts a local HTTP server;
5. opens the default browser.

The default address is:

```text
http://localhost:8543
```

Use a custom port with:

```python
engine.analyze(port=9000)
```

You can also load an existing `data.json` file passing the file path. `analyze()` serializes it before writing the file used by the UI:

```python
engine.analyze(json_path="data.json")
```

The server runs until interrupted with `Ctrl+C`.

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

- Only use this server on trusted local networks.
- The generated `data.json` contains source code from the analyzed
  repository.
- Stop the server with `Ctrl+C`.
