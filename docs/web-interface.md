# Web Interface

`RepoWhisper.serve_ui()` serves the bundled frontend locally.

```python
engine.serve_ui()
```

The method:

1. runs the analysis when JSON data was not supplied;
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
engine.serve_ui(json_data=json_data, port=9000)
```

The server runs until interrupted with `Ctrl+C`.

## Frontend data contract

The frontend expects the schema described in [Output Format](output.md).
`raw_modules` provides source code and explanations, while `notes` supplies
line-level annotations for the code viewer.

## Operational notes

- Only use this server on trusted local networks.
- The generated `data.json` can contain source code from the analyzed
  repository.
- Stop the server with `Ctrl+C`.
