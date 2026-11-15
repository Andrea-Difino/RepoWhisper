from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from langchain_core.documents import Document

from repowhisper.ingestion.ingestor import Ingestor
from repowhisper.ingestion.source_manager import SourceManager


def test_source_manager_local_and_missing(tmp_path):
    manager = SourceManager(str(tmp_path))
    assert manager.get_path() == str(tmp_path)

    with pytest.raises(ValueError, match="does not exist"):
        SourceManager(str(tmp_path / "missing")).get_path()


def test_source_manager_clone_success_and_cleanup(monkeypatch):
    manager = SourceManager("https://example.com/repo.git")
    cloned_path = "C:/temp/repo"
    clone_from = Mock()
    monkeypatch.setattr("repowhisper.ingestion.source_manager.Repo.clone_from", clone_from)
    monkeypatch.setattr(
        "repowhisper.ingestion.source_manager.tempfile.TemporaryDirectory",
        lambda prefix: SimpleNamespace(name=cloned_path, cleanup=Mock()),
    )

    assert manager.get_path() == cloned_path
    clone_from.assert_called_once_with("https://example.com/repo.git", cloned_path)
    manager.cleanup()
    assert manager.temp_dir is None


def test_source_manager_clone_failure_cleans_up(monkeypatch):
    manager = SourceManager("https://example.com/repo.git")
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


def test_ingestor_defaults_skips_unknown_and_splits(monkeypatch, tmp_path):
    raw_document = Document(page_content="def example():\n    return 1\n", metadata={})
    loader = Mock()
    loader.load.return_value = [raw_document]
    monkeypatch.setattr(
        "repowhisper.ingestion.ingestor.GenericLoader.from_filesystem",
        Mock(return_value=loader),
    )

    result = Ingestor(str(tmp_path)).ingest(["unknown", "PYTHON"])

    assert result
    loader.load.assert_called_once()


def test_ingestor_returns_empty_when_loader_has_no_documents(monkeypatch, tmp_path):
    loader = Mock()
    loader.load.return_value = []
    monkeypatch.setattr("repowhisper.ingestion.ingestor.GenericLoader.from_filesystem", Mock(return_value=loader))

    assert Ingestor(str(tmp_path)).ingest() == []
