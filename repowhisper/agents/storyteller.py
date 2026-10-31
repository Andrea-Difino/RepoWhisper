from typing import Any

from agents.base_agent import BaseAgent
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


class Storyteller(BaseAgent):

    def __init__(self, llm: BaseChatModel) -> None:
        self.llm = llm

        self.prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are an elite Technical Writer. Your goal is to synthesize the provided 
                architectural summary and module explanations into a beautiful, engaging technical overview.\n\n
                Instructions:\n
                1. Write a captivating introduction based on the Architecture Summary.\n
                2. Present the Module Explanations logically, highlighting how they connect.\n
                3. Ensure the tone is educational, motivating, and highly professional.\n
                4. Format the output in clean, structured Markdown.\n\n
                Raw Context Data:\n{context}
                """
            ),
            ("user","{query}")
        ])

    def analyze(self, query: str, context: Any) -> str:

        chain = self.prompt_template | self.llm

        result = chain.invoke({
            "query": query,
            "context": context
        })

        return str(result.content)