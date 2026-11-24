import time
from types import SimpleNamespace

import pytest
from utils.exceptions import ProviderError

from repowhisper.agents.architect import Architect
from repowhisper.agents.base_agent import BaseAgent
from repowhisper.agents.reviewer import LayaReviewer
from repowhisper.agents.storyteller import Storyteller


class FakeChain:
    def __init__(self, response):
        self.response = response

    def with_retry(self, **kwargs):
        return self

    def invoke(self, payload):
        self.payload = payload
        return self.response


class FakePrompt:
    def __init__(self, response):
        self.response = response

    def __or__(self, other):
        return FakeChain(self.response)


class FakeLLM:
    def __init__(self, response):
        self.response = response

    def with_structured_output(self, model):
        return self

    def __or__(self, other):
        return FakeChain(self.response)


def test_architect_reviewer_and_storyteller_analyze(monkeypatch):
    architect = Architect(object(), "junior")
    architect._prompt_template = FakePrompt(SimpleNamespace(content="architecture"))
    assert architect.analyze("query", "tree") == "architecture"

    storyteller = Storyteller(object(), "junior")
    storyteller._prompt_template = FakePrompt(SimpleNamespace(content="narrative"))
    assert storyteller.analyze("query", "context") == "narrative"


def test_laya_reviewer_normalizes_backbone_ids(tmp_path):
    assert LayaReviewer._is_valid_repo_id("Qwen/Qwen3.5-0.8B")
    assert not LayaReviewer._is_valid_repo_id("/invalid")
    assert LayaReviewer._normalize_backbone_repo_id("Qwen3.5-0.8B") == "Qwen/Qwen3.5-0.8B"
    assert LayaReviewer._normalize_backbone_repo_id("") is None


def test_laya_reviewer_parses_backbone_config(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(
        '{"base_model_name_or_path": "/kaggle/input/Qwen3.5-0.8B"}',
        encoding="utf-8",
    )
    assert LayaReviewer._parse_backbone_from_json_file(cfg) == "Qwen/Qwen3.5-0.8B"
    assert LayaReviewer._parse_backbone_from_json_file(tmp_path / "missing.json") is None


def test_laya_reviewer_evaluate_and_review():
    reviewer = LayaReviewer.__new__(LayaReviewer)

    class FakeAgent:
        def predict(self, draft, questions):
            label = "DEBUG" if "bug" in draft else "EXPLANATION"
            return {"answers": {"review_type": {"choice": label}}}

    reviewer.agent = FakeAgent()
    assert reviewer.evaluate("technical explanation") == "EXPLANATION"
    assert reviewer.review("technical explanation") is None
    assert reviewer.evaluate("bug hunt") == "DEBUG"
    assert reviewer.review("bug hunt") == LayaReviewer.DEBUG_FEEDBACK


def test_laya_reviewer_static_discovery_and_fetch(tmp_path, monkeypatch):
    assert not LayaReviewer._is_valid_repo_id("/invalid")
    assert LayaReviewer._normalize_backbone_repo_id("") is None

    cfg = tmp_path / "config.json"
    cfg.write_text(
        '{"base_model_name_or_path": "/kaggle/input/Qwen3.5-0.8B"}',
        encoding="utf-8",
    )
    assert LayaReviewer._parse_backbone_from_json_file(cfg) == "Qwen/Qwen3.5-0.8B"
    assert LayaReviewer._parse_backbone_from_json_file(tmp_path / "missing.json") is None

    class FakeApi:
        def repo_info(self, repo_id, files_metadata):
            return SimpleNamespace(
                siblings=[SimpleNamespace(size=10), SimpleNamespace(size=None)]
            )

    monkeypatch.setattr(
        "repowhisper.agents.reviewer.HfApi",
        lambda: FakeApi(),
    )
    assert LayaReviewer._fetch_total_repo_bytes(["a/b"]) == 10


def test_laya_reviewer_cache_and_instantiate(tmp_path, monkeypatch):
    reviewer = LayaReviewer.__new__(LayaReviewer)
    reviewer.cache_dir = tmp_path / "cache"
    reviewer.calibration_dir = tmp_path / "calibration"

    monkeypatch.setattr(
        "repowhisper.agents.reviewer.snapshot_download",
        lambda *args, **kwargs: str(tmp_path),
    )
    monkeypatch.setattr(
        LayaReviewer,
        "_discover_backbone_repo_id",
        lambda _self=None, _vega=None: None,
    )
    assert reviewer._ensure_models_cached()

    class FakeLayaAgent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setattr("repowhisper.agents.reviewer.laya.Agent", FakeLayaAgent)
    agent = reviewer._instantiate_vega_agent(use_offline_mode=False)
    assert agent.kwargs == {"vegaml": True}


def test_base_agent_run_chain_success_and_provider_errors(monkeypatch):
    class ConcreteAgent(BaseAgent):
        def analyze(self, query, context):
            return context

        def _get_prompt(self):
            return None

    agent = ConcreteAgent()
    chain = SimpleNamespace(invoke=lambda inputs: "ok")
    assert agent._run_chain(chain, {}) == "ok"

    class DailyLimitChain:
        def invoke(self, inputs):
            raise RuntimeError("tokens per day")

    with pytest.raises(ProviderError, match="daily token limit"):
        agent._run_chain(DailyLimitChain(), {}, max_retries=1)

    class ProviderChain:
        def invoke(self, inputs):
            raise RuntimeError("400 bad request")

    monkeypatch.setattr(time, "sleep", lambda _seconds: None)
    with pytest.raises(ProviderError, match="could not complete"):
        agent._run_chain(ProviderChain(), {}, max_retries=1)

    class RateLimitChain:
        def invoke(self, inputs):
            raise RuntimeError("429 rate limit; try again in 0.1s")

    monkeypatch.setattr(time, "sleep", lambda _seconds: None)
    with pytest.raises(ProviderError, match="could not complete"):
        agent._run_chain(RateLimitChain(), {}, max_retries=2)



