from typing import Any

from agents.base_agent import BaseAgent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


class Architect(BaseAgent):
    """
    Specialized agent that takes the project directory structure and outputs
    a clean, grounded architectural overview tailored to the user's level.
    """

    def __init__(self, llm: BaseChatModel, user_level: str):
        """
        Initializes the Architect agent.

        Args:
            llm: The language model to be used.
            user_level: Target developer seniority ('junior', 'mid', 'senior').
        """
        self.llm = llm
        self.user_level = user_level
        self.user_level_guidance = self._get_level_guidance(user_level)
        self._prompt_template = self._get_prompt()

    def _get_level_guidance(self, user_level: str) -> str:
        profiles = {
            "junior": (
                "Explain the role of each main directory in simple, clear terms so a newcomer "
                "understands how the folders fit together. Keep descriptions approachable."
            ),
            "mid": (
                "Focus on separation of concerns, module boundaries, and how data flows across layers. "
                "Keep descriptions crisp and direct."
            ),
            "senior": (
                "Be ultra-concise and high-signal. Summarize the architecture, stack, and layer boundaries "
                "in tight, dense bullet points without explaining basic software concepts."
            ),
        }
        return profiles.get(user_level.lower(), profiles["mid"])

    def _get_prompt(self) -> ChatPromptTemplate:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an elite Software Architect. Analyze the provided project directory tree and deduce the core architecture of the software.

                    STRICT FORMATTING & GROUNDING RULES (ZERO TOLERANCE):
                    1. NO MARKDOWN TABLES: NEVER use Markdown tables (`| ... |`). Tables overflow the UI container. Always use clean, scannable bulleted lists with **bold** labels instead.
                    2. NO WIDE ASCII DIAGRAMS: Do NOT draw multi-column ASCII box diagrams that risk horizontal overflow. If needed, use simple single-line arrow flows (e.g., `Input -> Transcription -> Extraction -> Output`).
                    3. ZERO HALLUCINATIONS ON CODE INTERNALS: You are only seeing the directory tree, NOT the source code inside the files. NEVER invent class names, function signatures, CLI flags, or file paths that do not appear verbatim in the provided tree. Refer only to actual directories and filenames visible in the tree.
                    4. NO META-HEADERS OR FOOTERS: Do NOT include lines like "Target audience: ..." or "End of architectural overview".

                    FOCUS AREAS:
                    - Primary programming languages, runtimes, and build/packaging tools visible in config files.
                    - Architectural pattern and layer organization based strictly on existing directories.
                    - Core domain purpose of the application.
                    - CI/CD or infrastructure components strictly if visible in the tree.

                    CALIBRATION FOR {user_level} LEVEL:
                    {user_level_guidance}

                    Project Structure:
                    {context}""",
                ),
                ("user", "{query}"),
            ]
        )
        return prompt

    def analyze(self, query: str, context: Any) -> str:
        chain = self._prompt_template | self.llm

        response = self._run_chain(
            chain,
            {
                "query": query,
                "context": context,
                "user_level": self.user_level.upper(),
                "user_level_guidance": self.user_level_guidance,
            },
        )

        return str(response.content)
