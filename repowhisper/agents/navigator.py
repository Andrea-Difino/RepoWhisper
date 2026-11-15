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
        description="A concise, high-value micro-insight (max 1-2 sentences)"
    )

class ModuleNavigationOutput(BaseModel):
    explanation: str = Field(
        description="Engaging, flowing technical prose explaining the module's role and data flow. Do NOT use monotonous bulleted lists."
    )
    line_whispers: list[LineWhisper] = Field(
        description="Targeted line-by-line micro-notes for the most critical, tricky, or interesting lines in the snippet."
    )

class CodeNavigator(BaseAgent):
    """
        Specialized agent responsible for interpreting and explaining specific 
        code fragments retrieved from the vector database.
    """

    def __init__(self, llm: BaseChatModel, user_level: str):
        """
        Initializes the CodeNavigatorAgent.
        
        Args:
            llm (BaseChatModel): The language model to be used.
        """
        self.llm = llm
        self.user_level = user_level
        self.user_level_prompt = self._get_code_navigator_prompt(user_level)
        self.prompt_template = ChatPromptTemplate.from_messages([
            ( 
                "system", 
                """You are the Code Navigator for RepoWhisper. Your goal is to guide a **{user_level}** developer through a specific code module so they truly understand how it works and how it fits into the broader system.

                WRITING RULES FOR `explanation` (ANTI-BOREDOM):
                1. FLOWING PROSE OVER LISTS: Do NOT write a mechanical bullet-point list summarizing every function or import one by one. Write 2 to 4 cohesive, engaging paragraphs of narrative technical prose.
                2. VISUAL ANCHORS: Use **bold text** strategically to highlight key classes, state transitions, and core concepts so the text is easy to scan.
                3. TELL THE STORY OF THE DATA: Explain what enters this file, how the code transforms or orchestrates it, and where it goes next.

                RULES FOR `line_whispers` (INTERACTIVE LINE NOTES):
                1. EXACT LINE MATCHING: The input code is prefixed with line numbers (e.g., `12 | ...`). Always use that exact integer for `line_number`.
                2. SELECTIVE & HIGH-SIGNAL: Do NOT annotate every single line (skip trivial imports or blank lines). Pick only the 3 to 7 most meaningful lines in the snippet.
                3. MICRO-FORMAT: Keep each `note` punchy, practical, and self-contained (1–2 sentences max), as it will appear in a compact tooltip/banner right below the code terminal when the user clicks that line.
                4. ZERO HALLUCINATIONS: Base everything strictly on the provided code.

                USER LEVEL CALIBRATION:
                {user_level_prompt}"""
            ),
            ("user", "{query}\n\n Code:\n{context}")
        ])

    def _get_code_navigator_prompt(self, user_level:str) -> str:
        level_profiles = {
            "junior": """
            - EXPLANATION STYLE: Use clear mental models and explain the "why" behind architectural choices without assuming prior mastery of advanced design patterns. Keep it encouraging and crystal clear.
            - LINE WHISPERS FOCUS: Highlight key syntax mechanics, library calls, environment variables needed at runtime, and common pitfalls or gotchas on specific lines.
            """,
            "mid": """
            - EXPLANATION STYLE: Focus on component integration, data contracts (inputs/outputs), state transitions, and error-handling boundaries.
            - LINE WHISPERS FOCUS: Point out side effects, data transformations, state mutations, implicit assumptions, and debugging tips tied to specific lines.
            """,
            "senior": """
            - EXPLANATION STYLE: Cut straight to architectural trade-offs, concurrency/memory implications, coupling, and extension points. Skip basic syntax explanations.
            - LINE WHISPERS FOCUS: Surface runtime bottlenecks, edge cases, thread-safety concerns, performance characteristics, or subtle abstraction leaks on critical lines.
            """
        }
        return level_profiles.get(user_level.lower(), level_profiles["mid"])

    def _format_code_with_line_numbers(self, code: str) -> str:
        lines = code.splitlines()
        return "\n".join(f"{idx + 1} | {line}" for idx, line in enumerate(lines))

    def analyze(self, query: str, context: Any) -> Any:
        """
        Processes the query against the code context using the injected LLM.
        """
        chain = self.prompt_template | self.llm.with_structured_output(ModuleNavigationOutput)

        numbered_code = self._format_code_with_line_numbers(context)

        response: ModuleNavigationOutput = chain.invoke({
            "context": numbered_code,
            "query": query,
            "user_level": self.user_level,
            "user_level_prompt": self.user_level_prompt
        }) # type: ignore
        

        return response.model_dump()
