import json
from types import SimpleNamespace
from typing import Any, cast

import pytest
from langchain_core.language_models.chat_models import BaseChatModel

from repowhisper import RepoWhisper, UserLevel
from repowhisper import repowhisper as facade_module


class FakeLLM:
    pass


@pytest.fixture(autouse=True)
def isolate_facade_console_and_reviewer(monkeypatch):
    class DummyReviewer:
        pass

    monkeypatch.setattr(RepoWhisper, "_print_ascii_art", lambda _self: None)
    monkeypatch.setattr(facade_module, "LayaReviewer", DummyReviewer)


def test_facade_initializes():
    engine = RepoWhisper(
        "owner/repository", cast(BaseChatModel, FakeLLM()), UserLevel.SENIOR
    )
    assert engine.user_level is UserLevel.SENIOR


def test_generate_documentation_success(monkeypatch, tmp_path):
    engine = RepoWhisper(str(tmp_path), cast(BaseChatModel, FakeLLM()))
    engine._source_manager = cast(
        Any, SimpleNamespace(        get_path=lambda: str(tmp_path), cleanup=lambda: None)
    )
    report = {
        "title": "RepoWhisper Analysis",
        "tree_structure": "root.py",
        "narrative": "Documentation narrative",
        "raw_modules": [
            {
                "file": "root.py",
                "explanation": "Explains root.py",
                "code_snippet": "print('ok')",
                "notes": {"1": "Entry point"},
            }
        ],
    }

    class Workflow:
        def __init__(self, **_kwargs):
            self.graph = SimpleNamespace(
                invoke=lambda _state: {"final_output_json": json.dumps(report)}
            )

    monkeypatch.setattr(facade_module, "AgentsWorkflow", Workflow)
    result = engine.generate_documentation()
    assert result is not None
    assert json.loads(result) == report


def test_generate_documentation_handles_keyboard_interrupt(monkeypatch, tmp_path):
    engine = RepoWhisper(str(tmp_path), cast(BaseChatModel, FakeLLM()))
    engine._source_manager = cast(
        Any, SimpleNamespace(        get_path=lambda: str(tmp_path), cleanup=lambda: None)
    )
    monkeypatch.setattr(
        engine._source_manager,
        "get_path",
        lambda: (_ for _ in ()).throw(KeyboardInterrupt),
    )
    assert engine.generate_documentation() is None


def test_analyze_handles_failed_generation(monkeypatch, tmp_path, capsys):
    engine = RepoWhisper(str(tmp_path), cast(BaseChatModel, FakeLLM()))
    monkeypatch.setattr(engine, "generate_documentation", lambda: None)
    engine.analyze()
    assert "Impossible to start interface" not in capsys.readouterr().out


def test_analyze_requires_ui_directory(monkeypatch, tmp_path):
    engine = RepoWhisper(str(tmp_path), cast(BaseChatModel, FakeLLM()))
    monkeypatch.setattr(facade_module.os.path, "dirname", lambda path: str(tmp_path))
    monkeypatch.setattr(facade_module.os.path, "exists", lambda path: False)
    with pytest.raises(FileNotFoundError):
        engine.analyze("{}")


def test_analyze_from_saved_report(monkeypatch, tmp_path):
    engine = RepoWhisper(str(tmp_path), cast(BaseChatModel, FakeLLM()))
    ui_dir = tmp_path / "ui_dist"
    ui_dir.mkdir()

    class Report:
        def model_dump_json(self, indent=2):
            return '{"title":"saved"}'

    class Server:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def serve_forever(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(
        facade_module.AnalysisJsonValidator,
        "validate_file",
        lambda path: Report(),
    )
    monkeypatch.setattr(facade_module.os.path, "dirname", lambda path: str(tmp_path))
    monkeypatch.setattr(facade_module.os.path, "abspath", lambda path: str(tmp_path / "facade.py"))
    monkeypatch.setattr(facade_module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(facade_module, "ThreadingHTTPServer", lambda *args, **kwargs: Server())
    monkeypatch.setattr(facade_module.webbrowser, "open", lambda url: True)

    engine.analyze(tmp_path / "report.json")
