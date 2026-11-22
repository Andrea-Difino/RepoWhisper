from repo_fixture import analysed_files, make_repo

from repowhisper.utils.facts_extractor import FactsExtractor
from repowhisper.utils.grounding_verifier import GroundingReport, GroundingVerifier


def make_verifier(tmp_path, evidence=""):
    make_repo(tmp_path)
    files, graph = analysed_files(tmp_path)
    facts = FactsExtractor(str(tmp_path)).extract(files, graph)
    return GroundingVerifier(facts, evidence)


def test_real_references_pass(tmp_path):
    v = make_verifier(tmp_path)
    text = (
        "`Engine` has a method `Engine.run()` and `helper`. See `app/core.py`, `core.py` and "
        "`app/core`. The CLI accepts `--dry-run` and reads `DEMO_TOKEN`; it uses `requests`, "
        "`argparse`, `str` and the `demo` script. CI is `ci.yaml` in `.github/workflows`."
    )
    report = v.verify(text)
    assert report.ok, report.unknown
    assert report.checked >= 10


def test_invented_references_are_reported_once_and_in_order(tmp_path):
    v = make_verifier(tmp_path)
    text = (
        "Uses `Planner` and `app/planner.py`, flag `--verbose`, `Engine.explode()`, "
        "`Planner` again and the file `settings.yaml`."
    )
    report = v.verify(text)
    assert report.unknown == ("Planner", "app/planner.py", "--verbose", "Engine.explode()", "settings.yaml")
    assert not report.ok
    assert "`Planner`" in report.feedback() and "CORRECTION REQUIRED" in report.feedback()


def test_commands_numbers_snippets_and_fenced_blocks_are_not_judged(tmp_path):
    v = make_verifier(tmp_path)
    text = (
        "Run `uv sync --extra groq`, needs `3.12`, set `x = Fake(1)` or install `demo[openai]`.\n"
        "```python\nfrom nowhere import Ghost\n`Ghost`\n```\n"
    )
    report = v.verify(text)
    assert report.ok and report.checked == 0


def test_names_present_in_the_evidence_text_are_accepted(tmp_path):
    v = make_verifier(tmp_path, evidence="- `app/core.py`: Applies the `Sanitizer` strategy")
    assert v.verify("The `Sanitizer` strategy").ok
    assert not make_verifier(tmp_path / "other").verify("The `Sanitizer` strategy").ok


def test_report_object():
    assert GroundingReport(checked=0, unknown=()).ok


def test_brand_casing_of_a_real_library_is_not_a_false_positive(tmp_path):
    v = make_verifier(tmp_path)
    assert v.verify("Built with `Requests` and `Langchain-Core`.").ok
    assert not v.verify("Built with `Redis`.").ok
