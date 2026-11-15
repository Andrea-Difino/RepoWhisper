from typing import Any

from agents.base_agent import BaseAgent
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


class Storyteller(BaseAgent):

    def __init__(self, llm: BaseChatModel, user_level: str) -> None:
        self.llm = llm
        self.user_level = user_level

        self.prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are the Lead Technical Architect for RepoWhisper. Your mission is to produce a clear, accurate, and engaging architectural overview of the repository based STRICTLY on the provided source code and context.

                STRICT GUARDRAILS (ZERO TOLERANCE):
                1. NO CLI OR PARAMETER HALLUCINATIONS: NEVER invent command-line flags (e.g., --dry-run, --input), CLI subcommands, environment variables, or file paths unless they are explicitly defined in the analyzed code. If usage commands are not present in the context, omit the "Getting Started" section completely rather than guessing.
                2. NO UNSOLICITED CONSULTING OR FLUFF: Document the codebase AS IT EXISTS today. You are strictly forbidden from adding opinionated sections, self-praise, or future roadmaps. NEVER generate sections such as "Why This Architecture Works", "Next Steps for the Team", "Future Improvements", "Recommendations", or motivational "Closing Thoughts".
                3. FACTUAL GROUNDING: Every component, library, and data flow you describe must map directly to the analyzed files.
                4. USER LEVEL: Tailor the length and depth to the user level: (Junior = detailed and educational, Mid = balanced, Senior = highly concise and direct).\n

                STRUCTURE & TONE:
                - Write in crisp, authoritative, and accessible technical English.
                - Focus exclusively on:
                1. **Core Purpose**: What the software actually does.
                2. **System Architecture**: How the real modules and layers are organized and what each is responsible for.
                3. **Data Flow**: How inputs are transformed step-by-step into outputs across the existing pipeline.\n\n
                User level: {user_level}\n
                Context Data:\n{context}
                """
            ),
            ("user","{query}")
        ])

    def analyze(self, query: str, context: Any) -> str:

        chain = self.prompt_template | self.llm

        result = chain.invoke({
            "query": query,
            "context": context,
            "user_level": self.user_level
        })

        return str(result.content)