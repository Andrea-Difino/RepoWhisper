# Input Sources

## Local repositories

Pass an existing directory:

```python
engine = RepoWhisper(
    source_target=r"C:\Projects\my-repository",
    llm=llm,
)
```

The path must exist. Otherwise `SourceManager.get_path()` raises `ValueError`.

## Remote repositories

Pass an HTTP(S) Git URL:

```python
engine = RepoWhisper(
    source_target="https://github.com/owner/project",
    llm=llm,
)
```

RepoWhisper clones the repository to a temporary directory before analysis.
Clone failures are reported as `RuntimeError`; private repositories require Git
credentials to be configured in the environment.

## Files included in analysis

The dependency tracer currently analyzes Python imports and ignores common
non-source directories such as:

- `.git`;
- virtual environments;
- `node_modules`;
- test directories;
- build and distribution directories.
