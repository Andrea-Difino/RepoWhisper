from types import SimpleNamespace

from repowhisper.agents.architect import Architect
from repowhisper.agents.navigator import CodeNavigator, ModuleNavigationOutput
from repowhisper.agents.reviewer import Reviewer
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

    reviewer = Reviewer(object())
    reviewer._prompt_template = FakePrompt(SimpleNamespace(content='{"response":"APPROVED"}'))
    assert reviewer.analyze("query", "draft") == '{"response":"APPROVED"}'

    storyteller = Storyteller(object(), "junior")
    storyteller._prompt_template = FakePrompt(SimpleNamespace(content="narrative"))
    assert storyteller.analyze("query", "context") == "narrative"



