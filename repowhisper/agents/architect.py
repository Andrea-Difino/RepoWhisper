from typing import Any

from agents.base_agent import BaseAgent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


class Architect(BaseAgent):
    """
    Specialized agent that takes grounded evidence about the project (directory tree,
    statically extracted facts and short per-module notes) and outputs a clean,
    architectural overview tailored to the user's level.
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
                    """You are an elite Software Architect. You receive EVIDENCE extracted from a repository: a directory tree, a facts sheet computed by static analysis of the code (authoritative), and short per-module notes. Deduce the core architecture of the software from this evidence ONLY.

                    STRICT FORMATTING & GROUNDING RULES (ZERO TOLERANCE):
                    1. NO MARKDOWN TABLES: NEVER use Markdown tables (`| ... |`). Tables overflow the UI container. Always use clean, scannable bulleted lists with **bold** labels instead.
                    2. NO WIDE ASCII DIAGRAMS: Do NOT draw multi-column ASCII box diagrams that risk horizontal overflow. If needed, use simple single-line arrow flows (e.g., `Input -> Transcription -> Extraction -> Output`).
                    3. GROUND EVERY CLAIM IN THE EVIDENCE: You do NOT see the source code. Mention only directories, files, classes, functions, libraries, CLI flags and environment variables that appear verbatim in the evidence, and write each of them inside `backticks` exactly as written there. If something is not in the evidence, do not mention it and do not guess: say nothing rather than speculate.
                    4. NO META-HEADERS OR FOOTERS: Do NOT include lines like "Target audience: ..." or "End of architectural overview".

                    FOCUS AREAS:
                    - Primary programming languages, runtimes, and build/packaging tools listed in the facts sheet.
                    - Architectural pattern and layer organization based strictly on the existing modules and on which modules import which.
                    - Core domain purpose of the application (use the README excerpt and the module notes).
                    - CI/CD or infrastructure components strictly if listed in the facts sheet.

                    CALIBRATION FOR {user_level} LEVEL:
                    {user_level_guidance}

                    EVIDENCE:
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
