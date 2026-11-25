from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from .base_agent import BaseAgent


class Storyteller(BaseAgent):
    def __init__(self, llm: BaseChatModel, user_level: str) -> None:
        """
        Initializes the StorytellerAgent.

        Args:
            llm: The language model to be used.
            user_level: User level decided by the user
        """
        self.llm = llm
        self.user_level = user_level

        self._prompt_template = self._get_prompt()

    def _get_prompt(self) -> ChatPromptTemplate:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                You are the Lead Technical Architect for RepoWhisper. Your mission is to produce a clear, accurate, and engaging architectural overview of the repository based STRICTLY on the EVIDENCE provided below.

                The EVIDENCE contains: (1) a facts sheet computed by static analysis of the code (authoritative), (2) short notes about each module, grouped by directory, and (3) a draft architectural overview written from that same evidence. The draft may contain mistakes: when it disagrees with the facts sheet or the module notes, trust the facts sheet and the module notes.

                STRICT GUARDRAILS (ZERO TOLERANCE):
                1. NO CLI OR PARAMETER HALLUCINATIONS: NEVER invent command-line flags (e.g., --dry-run, --input), CLI subcommands, environment variables, or file paths unless they appear in the evidence. If usage commands are not present in the evidence, omit the "Getting Started" section completely rather than guessing.
                2. NO UNSOLICITED CONSULTING OR FLUFF: Document the codebase AS IT EXISTS today. You are strictly forbidden from adding opinionated sections, self-praise, or future roadmaps. NEVER generate sections such as "Why This Architecture Works", "Next Steps for the Team", "Future Improvements", "Recommendations", or motivational "Closing Thoughts".
                3. FACTUAL GROUNDING: Every component, library, and data flow you describe must map directly to the evidence. Write every file, directory, class, function, library, flag or environment variable inside `backticks`, exactly as it appears in the evidence. If a detail is not in the evidence, leave it out.
                4. USER LEVEL: Tailor the length and depth to the user level: (Junior = detailed and educational, Mid = balanced, Senior = highly concise and direct).

                STRUCTURE & TONE:
                - Write in crisp, authoritative, and accessible technical English.
                - Focus exclusively on:
                1. **Core Purpose**: What the software actually does.
                2. **System Architecture**: How the real modules and layers are organized and what each is responsible for.
                3. **Data Flow**: How inputs are transformed step-by-step into outputs across the existing pipeline.

                User level: {user_level}

                EVIDENCE:
                {context}
                """,
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
                "user_level": self.user_level
            }
        )

        return str(response.content)
