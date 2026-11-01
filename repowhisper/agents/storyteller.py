from typing import Any

from agents.base_agent import BaseAgent
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


class Storyteller(BaseAgent):

    def __init__(self, llm: BaseChatModel, user_level: str) -> None:
        self.llm = llm
        self.user_level = user_level

        self.prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are an elite Technical Writer crafting the introduction for a modern, interactive software documentation Web UI.\n\n
                Your task is to synthesize the project's architectural summary into a cohesive, engaging overview.\n\n
                STRICT CONSTRAINTS:\n
                - Tailor the length and depth to the user level: (Junior = detailed and educational, Mid = balanced, Senior = highly concise and direct).\n
                - DO NOT create a module-by-module breakdown or list individual files. The frontend UI will render individual modules dynamically using separate JSON data.\n
                - Focus ONLY on the project's overarching purpose, the core architectural design patterns, and the general data flow.\n
                - Use a professional, motivating tone.\n
                - Format the output in clean Markdown.\n\n
                User level: {user_level}\n
                Context Data:\n{context}
                """
            ),
            ("user","{query}")
        ])

    def analyze(self, query: str, context: Any) -> str:

        chain = self.prompt_template | self.llm

        result = chain.invoke({
            "query": query,
            "context": context,
            "user_level": self.user_level
        })

        return str(result.content)