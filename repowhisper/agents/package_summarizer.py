from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from .base_agent import BaseAgent


class PackageSummarizer(BaseAgent):
    """
    Small helper agent used ONLY when the per-file notes of a repository do not fit the
    token budget. It compresses the notes of one directory into a few factual sentences.

    It never sees raw source code, only the short notes already produced for each file,
    so every call is small and cheap.
    """

    def __init__(self, llm: BaseChatModel):
        """
        Args:
            llm: The language model to be used.
        """
        self.llm = llm
        self._prompt_template = self._get_prompt()

    def _get_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You compress notes about ONE part of a software repository into a short, factual summary.

                    STRICT RULES:
                    1. Write at most 3 sentences (about 60 words), plain prose, no bullet list, no preamble.
                    2. Use ONLY the information in the notes. Never add technologies, behaviours, flags or file names that are not in the notes.
                    3. Keep file, class and function names exactly as written, inside `backticks`.
                    4. Say what the part is responsible for and how its files relate to each other.""",
                ),
                ("user", "Part of the repository: {query}\n\nNotes:\n{context}"),
            ]
        )

    def analyze(self, query: str, context: Any) -> str:
        """
        Args:
            query (str): label of the part being summarized (for example `agents/`).
            context (Any): the notes to compress.

        Returns:
            str: the short summary.
        """
        chain = self._prompt_template | self.llm
        response = self._run_chain(chain, {"query": query, "context": context})
        return str(response.content)
