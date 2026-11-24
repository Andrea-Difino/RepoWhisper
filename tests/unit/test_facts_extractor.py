from repo_fixture import analysed_files, make_repo, write

from repowhisper.utils.facts_extractor import FactsExtractor, pagerank


def extract(tmp_path):
    make_repo(tmp_path)
    files, graph = analysed_files(tmp_path)
    return FactsExtractor(str(tmp_path)).extract(files, graph)


def test_extracts_symbols_imports_and_main_guard(tmp_path):
    facts = extract(tmp_path)

    core = facts.files["app/core.py"]
    assert core.docstring == "Core cleaning engine."
    assert "class Engine [run]" in core.symbols  # private methods are not listed
    assert "def helper(data, mode)" in core.symbols

    cli = facts.files["app/cli.py"]
    assert cli.external_imports == {"requests"}  # stdlib and internal imports are excluded
    assert cli.has_main_guard is True
    assert facts.files["app/util.py"].has_main_guard is False


def test_graph_fan_in_and_pagerank_prefer_the_central_module(tmp_path):
    facts = extract(tmp_path)

    assert facts.fan_in["app/core.py"] == 2  # imported by cli.py and util.py
    assert facts.fan_in["app/cli.py"] == 0
    assert max(facts.rank, key=facts.rank.get) == "app/core.py"
    assert abs(sum(facts.rank.values()) - 1.0) < 1e-6


def test_pagerank_handles_empty_cycles_and_dangling_nodes():
    assert pagerank({}) == {}
    cyc = pagerank({"a": ["b"], "b": ["a"], "c": []})
    assert abs(sum(cyc.values()) - 1.0) < 1e-6
    assert abs(cyc["a"] - cyc["b"]) < 1e-9


def test_sheet_contains_project_readme_ci_and_core_facts(tmp_path):
    sheet = extract(tmp_path).sheet

    assert "demo-app" in sheet and "Demo application that cleans data." in sheet
    assert "cleans and validates tabular data" in sheet  # README text, without badges/headings
    assert "badge" not in sheet and "Install" not in sheet
    assert "`demo` -> `app.cli:main`" in sheet
    assert "`app/cli.py`" in sheet  # run-as-script / entry module
    assert "`app/core.py` (2)" in sheet  # core module with fan-in
    assert "`requests`" in sheet  # third-party, from imports and from pyproject
    assert "`--dry-run`" in sheet
    assert "`ci.yaml`" in sheet
    assert "`extra`" in sheet  # optional extras


def test_vocabulary_covers_args_attributes_env_vars_and_paths(tmp_path):
    facts = extract(tmp_path)

    for name in ("Engine", "run", "strict", "mode", "helper", "_private", "DEMO_TOKEN", "requests"):
        assert name in facts.known_identifiers
    assert "--dry-run" in facts.known_flags
    assert "app/core.py" in facts.known_paths and "app" in facts.known_paths
    assert ".github/workflows/ci.yaml" in facts.known_paths


def test_unparsable_and_missing_files_are_tolerated(tmp_path):
    write(tmp_path / "broken.py", "def (:\n")
    facts = FactsExtractor(str(tmp_path)).extract(["broken.py", "missing.py"], {})
    assert set(facts.files) == {"broken.py", "missing.py"}
    assert facts.files["broken.py"].symbols == []


def test_sheet_stays_bounded_on_large_repositories(tmp_path):
    files = []
    for i in range(300):
        rel = f"pkg{i % 40}/mod{i}.py"
        write(tmp_path / rel, f"import lib{i}\n\n\ndef f{i}(a, b):\n    return a\n")
        files.append(rel)
    facts = FactsExtractor(str(tmp_path)).extract(files, {})
    assert len(facts.sheet) < 4000  # lists are capped, size does not grow with the repo
