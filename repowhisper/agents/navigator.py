from typing import Any

from agents.base_agent import BaseAgent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class LineWhisper(BaseModel):
    line_number: int = Field(
        description="The exact 1-based line number from the numbered code snippet."
    )
    note: str = Field(
        description="A concise, high-value micro-insight (max 1-2 sentences)."
    )


class ModuleNavigationOutput(BaseModel):
    explanation: str = Field(
        description="Engaging, flowing technical prose explaining the module's role and data flow, strictly respecting the target length for the user level."
    )
    line_whispers: list[LineWhisper] = Field(
        description="Targeted line-by-line micro-notes for the most critical lines, strictly respecting the target count for the user level."
    )


class CodeNavigator(BaseAgent):
    """
    Specialized agent responsible for interpreting and explaining specific
    code fragments read from the repository.
    """

    def __init__(self, llm: BaseChatModel, user_level: str):
        """
        Initializes the CodeNavigator agent.

        Args:
            llm: The language model to be used.
            user_level: User level decided by the user ('junior', 'mid', 'senior').
        """
        self.llm = llm
        self.user_level = user_level
        self.user_level_prompt = self._get_code_navigator_prompt(user_level)
        self._prompt_template = self._get_prompt()

    def _get_prompt(self) -> ChatPromptTemplate:
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are the Code Navigator for RepoWhisper. Your goal is to guide a **{user_level}** developer through a specific code module so they understand how it works and how it fits into the system.

                GENERAL WRITING RULES:
                1. FLOWING PROSE OVER LISTS: Do NOT write a mechanical bullet-point list summarizing every function or import one by one. Write cohesive, engaging narrative technical prose.
                2. VISUAL ANCHORS: Use **bold text** strategically to highlight key classes, state transitions, and core concepts so the text is easy to scan.
                3. EXACT LINE MATCHING: In `line_whispers`, the input code is prefixed with line numbers (e.g., `12 | ...`). Always use that exact integer for `line_number`.
                4. ZERO HALLUCINATIONS: Base everything strictly on the provided code.

                USER LEVEL CALIBRATION & STRICT LENGTH BUDGET:
                {user_level_prompt}""",
            ),
            ("user", "{query}\n\nCode:\n{context}"),
        ])
        return prompt

    def _get_code_navigator_prompt(self, user_level: str) -> str:
        level_profiles = {
            "junior": """
            - LENGTH & STRUCTURE: Write **3 to 4 clear, well-paced paragraphs** (~220-300 words). Walk through the module's purpose, its main methods, and conclude with a short takeaway on how it protects the rest of the pipeline.
            - EXPLANATION STYLE: Use clear mental models and explain the "why" behind architectural choices without assuming prior mastery of design patterns. Keep it encouraging and crystal clear.
            - LINE WHISPERS (5 to 7 notes): Highlight key syntax mechanics, library calls, fallback behaviors, and common pitfalls on specific lines.
            """,
            "mid": """
            - LENGTH & STRUCTURE: Write **2 tight, focused paragraphs** (~130-180 words). Do NOT include an introductory filler sentence or a concluding "Overall, this module..." summary paragraph.
            - EXPLANATION STYLE: Focus directly on component integration, input/output contracts, state transitions, and error-handling boundaries.
            - LINE WHISPERS (3 to 5 notes): Point out side effects, data transformations, implicit assumptions, and fallback edge cases tied to specific lines.
            """,
            "senior": """
            - LENGTH & STRUCTURE: Be **ultra-concise**. Write **1 single, high-density paragraph** (max 90-120 words). Skip obvious method-by-method walkthroughs and NEVER write a summary/wrap-up sentence.
            - EXPLANATION STYLE: Cut straight to architectural trade-offs, I/O or memory implications, coupling, fallback semantics, and extension points.
            - LINE WHISPERS (2 to 3 notes ONLY): Annotate ONLY non-obvious lines involving runtime edge cases, OS/codec quirks, concurrency, or subtle abstraction leaks. Skip routine logic.
            """,
        }
        return level_profiles.get(user_level.lower(), level_profiles["mid"])

    def _format_code_with_line_numbers(self, code: str) -> str:
        lines = code.splitlines()
        return "\n".join(f"{idx + 1} | {line}" for idx, line in enumerate(lines))

    def analyze(self, query: str, context: Any) -> Any:
        """
        Processes the query against the code context using the injected LLM.
        """
        chain = (
            self._prompt_template | self.llm.with_structured_output(ModuleNavigationOutput)
        ).with_retry(stop_after_attempt=6)

        numbered_code = self._format_code_with_line_numbers(context)

        response: ModuleNavigationOutput = chain.invoke({
            "context": numbered_code,
            "query": query,
            "user_level": self.user_level.upper(),
            "user_level_prompt": self.user_level_prompt,
        })  # type: ignore

        return response.model_dump()