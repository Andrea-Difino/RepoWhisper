from typing import Any

from agents.base_agent import BaseAgent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


class CodeNavigator(BaseAgent):
    """
        Specialized agent responsible for interpreting and explaining specific 
        code fragments retrieved from the vector database.
    """

    def __init__(self, llm: BaseChatModel):
        """
        Initializes the CodeNavigatorAgent.
        
        Args:
            llm (BaseChatModel): The language model to be used.
        """
        self.llm = llm
        self.prompt_template = ChatPromptTemplate.from_messages([
            ( 
                "system", 
                """You are an elite Senior Software Engineer. Your task is to provide a concise,
                high-level logical summary of the provided code file.\n\n
                STRICT CONSTRAINTS:\n
                - Maximum length: 5 or 7 short sentences.\n
                - DO NOT explain imports, arguments, or basic boilerplate.\n
                - DO NOT reproduce or quote any code blocks.\n
                - The explanation should be enough to understand the code.\n
                - Use a direct, educational tone.\n\n
                Context Data:\n{context}"""
            ),
            ("user", "{query}")
        ])

    def analyze(self, query: str, context: Any) -> str:
        """
        Processes the query against the code context using the injected LLM.
        """
        chain = self.prompt_template | self.llm

        response = chain.invoke({
            "context": context,
            "query": query
        })

        return str(response.content)
