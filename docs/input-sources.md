# Input Sources

## Remote repositories

Pass an HTTP(S) Git URL:

```python
engine = RepoWhisper(
    source_target="https://github.com/owner/project",
    llm=llm,
)
```

RepoWhisper clones the repository to a temporary directory before analysis.
Clone failures are reported as `RepositoryCloneError`; private repositories require Git
credentials to be configured in the environment.

## Files included in analysis

RepoWhisper is currently for **Python code analysis only**. It does not provide
equivalent support for JavaScript, TypeScript, Java, Go, Rust, or other languages.

The dependency tracer currently analyzes Python imports and ignores common
non-source directories such as:

- `.git`;
- virtual environments;
- `node_modules`;
- test directories;
- build and distribution directories.
