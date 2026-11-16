from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from repowhisper.ingestion.source_manager import SourceManager


def test_source_manager_rejects_non_github_targets(tmp_path):
    with pytest.raises(ValueError, match="valid link to a github repo"):
        SourceManager(str(tmp_path)).get_path()

    with pytest.raises(ValueError, match="valid link to a github repo"):
        SourceManager(str(tmp_path / "missing")).get_path()


def test_source_manager_clone_success_and_cleanup(monkeypatch):
    manager = SourceManager("https://github.com/example/repo.git")
    cloned_path = "C:/temp/repo"
    clone_from = Mock()
    monkeypatch.setattr("repowhisper.ingestion.source_manager.Repo.clone_from", clone_from)
    monkeypatch.setattr(
        "repowhisper.ingestion.source_manager.tempfile.TemporaryDirectory",
        lambda prefix: SimpleNamespace(name=cloned_path, cleanup=Mock()),
    )

    assert manager.get_path() == cloned_path
    clone_from.assert_called_once_with("https://github.com/example/repo.git", cloned_path)
    manager.cleanup()
    assert manager.temp_dir is None


def test_source_manager_clone_failure_cleans_up(monkeypatch):
    manager = SourceManager("https://github.com/example/repo.git")
    temporary = SimpleNamespace(name="C:/temp/repo", cleanup=Mock())
    monkeypatch.setattr("repowhisper.ingestion.source_manager.tempfile.TemporaryDirectory", lambda prefix: temporary)
    error = __import__("git.exc", fromlist=["GitCommandError"]).GitCommandError(
        "clone", 128, stderr="failure"
    )
    monkeypatch.setattr("repowhisper.ingestion.source_manager.Repo.clone_from", Mock(side_effect=error))

    with pytest.raises(RuntimeError, match="Git exit code: 128"):
        manager.get_path()
    temporary.cleanup.assert_called_once()
    assert manager.temp_dir is None


