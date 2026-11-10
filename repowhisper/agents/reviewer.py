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
                You must respond using JSON. The answer should have this structure:\n
                {{
                    "response": "<VIOLATION/APPROVED>"
                    "feedback": "<a very short feedback to fix the explanation if VIOLATION>"
                }}\n\n
                If the text violates the Golden Rule, the 'response' field MUST contain VIOLATION and a short advice in the 'feedback' field.\n
                If the text is right, the 'response' field MUST contain APPROVED and the 'feedback' field an empty string."""
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