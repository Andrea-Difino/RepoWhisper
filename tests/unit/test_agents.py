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


def test_navigator_prompts_formatting_and_analyze():
    navigator = CodeNavigator(FakeLLM(None), "junior")
    assert "clear mental models" in navigator.user_level_prompt
    assert "integration" in CodeNavigator(FakeLLM(None), "mid").user_level_prompt
    assert "architectural trade-offs" in CodeNavigator(FakeLLM(None), "senior").user_level_prompt
    assert "component integration" in CodeNavigator(FakeLLM(None), "other").user_level_prompt

    navigator._prompt_template = FakePrompt(
        ModuleNavigationOutput(explanation="explained", line_whispers=[])
    )
    result = navigator.analyze("explain", "line one\nline two")
    assert result == {"explanation": "explained", "line_whispers": []}
    assert navigator._format_code_with_line_numbers("a\nb") == "1 | a\n2 | b"
