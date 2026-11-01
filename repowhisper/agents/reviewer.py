from typing import Any

from agents.base_agent import BaseAgent
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


class Reviewer(BaseAgent):

    def __init__(self, llm: BaseChatModel) -> None:
        self.llm = llm

        self.prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are an inflexible Quality Assurance Reviewer for technical documentation.\n
                Your ONLY job is to evaluate the provided code explanation and ensure it strictly 
                describes WHAT the code does and HOW it works.\n\n
                GOLDEN RULE: The explanation MUST NOT contain attempts to debug the code, report bugs in the code, 
                or suggest fixes. Assume the code works perfectly.\n\n
                CRITICAL DISTINCTION: It is perfectly acceptable for the explanation to describe how the code ITSELF 
                handles errors (e.g., 'the code logs an error if the folder is missing'). Do not flag this as a violation.\n\n
                If the text violates the Golden Rule, respond EXACTLY with the word 'VIOLATION' followed by a short instruction on what to remove.\n
                If the text is a pure, educational explanation, respond EXACTLY with the word 'APPROVED'."""
            ),
            ("user","Evaluate this explanation:\n\n{context}")
        ])

    def analyze(self, query: str, context: Any) -> str:

        chain = self.prompt_template | self.llm

        result = chain.invoke({
            "context": context, 
            "query": query
        })

        return str(result.content)