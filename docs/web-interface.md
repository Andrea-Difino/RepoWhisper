# Web Interface

`RepoWhisper.serve_ui()` serves the bundled frontend locally.

```python
engine.serve_ui()
```

The method:

1. runs the analysis when JSON data path is not supplied;
2. writes the JSON to `repowhisper/ui_dist/data.json`;
3. changes into the bundled UI directory;
4. starts a local HTTP server;
5. opens the default browser.

The default address is:

```text
http://localhost:8543
```

Use a custom port with:

```python
engine.serve_ui(port=9000)
```

You can also load an existing `data.json` file passing the file path. `serve_ui()` serializes it before writing the file used by the UI:

```python
engine.serve_ui(json_path="data.json")
```

The server runs until interrupted with `Ctrl+C`.

In an application entry point, handle failures around `serve_ui()`:

```python
try:
    engine.serve_ui()
except Exception as exc:
    print(f"RepoWhisper failed: {exc}")
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
