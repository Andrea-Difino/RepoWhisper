from typing import Any

from agents.base_agent import BaseAgent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


class Architect(BaseAgent):

    def __init__(self, llm: BaseChatModel):
        """
                Initializes the ArchitectAgent.
                
                Args:
                    llm: The language model to be used.
                    user_level: User level decided by the user
                """
        self.llm = llm
        self._prompt_template = self._get_prompt()

    def _get_prompt(self) -> ChatPromptTemplate:
        prompt = ChatPromptTemplate.from_messages([
            ("system","You are an elite Software Architect. Your task is to analyze the provided project directory tree and deduce the core architecture of the software.\n\n Focus on:\n 1. The primary programming languages and frameworks used.\n 2. The likely architectural pattern (e.g., MVC, Microservices, Monolith, Clean Architecture).\n 3. The primary purpose or domain of the application.\n 4. Key infrastructure components (e.g., Docker, CI/CD pipelines, databases) if visible.\n\n Do not invent information. Base your analysis strictly on the provided file tree. Provide a structured, executive summary.\n\n Project Structure:\n{context}"),
            ("user", "{query}")
        ])

        return prompt

    def analyze(self, query: str, context: Any) -> str:

        chain = (self._prompt_template | self.llm).with_retry(stop_after_attempt=6)

        response = chain.invoke({
            "query": query,
            "context": context,
        })

        return str(response.content)