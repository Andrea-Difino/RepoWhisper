# Limitations and Troubleshooting

## Current limitations

- The dependency tracer currently analyzes Python imports.
- The quality of generated explanations depends on the selected LLM.
- Large repositories can require substantial time, memory, and model tokens.
- The bundled HTTP server is intended for local use, not production hosting.
- `serve_ui()` writes generated source data into the bundled UI directory.

## Common issues

### No parsable code found

Confirm that the target contains `.py` files and that the path or Git URL is
correct.

### Git clone failure

Check that Git is installed and that credentials are available for private
repositories.

### Missing provider package

Install the matching optional extra, for example:

```powershell
uv sync --extra groq
```

### Missing provider key

Set the provider key in the environment before creating the chat model. Never
hard-code or commit the key.

### Documentation import errors

Run MkDocs from the repository root and use the project environment:

```powershell
.\.venv\Scripts\mkdocs.exe build --strict
```
