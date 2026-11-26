import posixpath
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

from tqdm import tqdm

from ..utils.token_budget import TokenUtilities, arrange_edges_first

# A summarizer takes (label, text) and returns a short factual summary of `text`.
Summarizer = Callable[[str, str], str]

_MAX_DEPS_SHOWN = 6
_KEY_FILES_SHOWN = 3
_OTHER_FILES_SHOWN = 10


@dataclass(frozen=True)
class FileCard:
    """A compact, one-line description of a file used as prompt evidence."""

    path: str
    summary: str = ""
    symbols: tuple[str, ...] = ()
    deps: tuple[str, ...] = ()
    rank: float = 0.0

    def render(self) -> str:
        head = f"- `{self.path}`"
        if self.summary:
            head += f": {self.summary}"
        parts = [head]
        if self.symbols:
            parts.append("defines: " + "; ".join(self.symbols))
        if self.deps:
            shown = ", ".join(self.deps[:_MAX_DEPS_SHOWN])
            more = len(self.deps) - _MAX_DEPS_SHOWN
            parts.append("imports: " + shown + (f" (+{more} more)" if more > 0 else ""))
        return " | ".join(parts)


@dataclass
class _Block:
    """All the evidence belonging to one directory (or to a merge of directories)."""

    name: str
    cards: list[FileCard]
    body: str
    summarized: bool = False
    tokens: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.refresh()

    @property
    def rank(self) -> float:
        return sum(card.rank for card in self.cards)

    @property
    def heading(self) -> str:
        return f"## `{self.name}/` ({len(self.cards)} files)"

    def render(self) -> str:
        return f"{self.heading}\n{self.body}"

    def refresh(self) -> None:
        self.tokens = TokenUtilities.estimate_tokens(self.render())


class EvidencePacker:
    """
    Packs per-file cards into a text that is guaranteed to fit a token budget.

    Strategy (a budget-aware, bottom-up "collapse", like a map-reduce summarization
    that follows the directory structure instead of arbitrary chunks):

      1. Group cards by directory. If everything fits the budget, nothing else happens
         and zero LLM calls are made.
      2. Otherwise collapse directories into short summaries, LEAST important first
         (importance = PageRank of the files they contain), and stop as soon as the
         text fits. The most central modules therefore keep their full detail.
      3. If every directory is already collapsed and it is still too big, lift the
         blocks one directory level up and repeat (recursive collapse).
      4. A final deterministic trim guarantees the budget is respected.

    The collapse is done with the injected `summarizer` (an LLM call per block, each
    call bounded by `chunk_budget`). Without a summarizer, or if it fails, a
    deterministic summary (key files + file names) is used, so packing never crashes
    the pipeline.
    """

    def __init__(
        self,
        summarizer: Summarizer | None = None,
        chunk_budget: int = 2500,
        max_rounds: int = 3,
    ):
        self.summarizer = summarizer
        self.chunk_budget = chunk_budget
        self.max_rounds = max_rounds
        self.llm_calls = 0

    def pack(self, cards: list[FileCard], budget: int) -> str:
        """
        Args:
            cards (list[FileCard]): one card per analysed file.
            budget (int): maximum estimated tokens of the returned text.

        Returns:
            str: grouped module notes, important areas placed at the start and at the end.
        """
        if not cards:
            return ""

        groups: dict[str, list[FileCard]] = defaultdict(list)
        for card in cards:
            groups[posixpath.dirname(card.path) or "."].append(card)

        blocks = [
            _Block(name, group, self._render_cards(group))
            for name, group in sorted(groups.items())
        ]

        while self._total(blocks) > budget:
            pending = [b for b in blocks if not b.summarized]
            if pending:
                self._summarize(min(pending, key=lambda b: b.rank))
                continue
            lifted = self._lift(blocks)
            if lifted is None:
                break
            blocks = lifted

        blocks = self._hard_trim(blocks, budget)
        return self._render(blocks)

    @staticmethod
    def _total(blocks: list[_Block]) -> int:
        return sum(b.tokens for b in blocks)

    @staticmethod
    def _render_cards(cards: list[FileCard]) -> str:
        ordered = sorted(cards, key=lambda c: (-c.rank, c.path))
        return "\n".join(card.render() for card in ordered)

    @staticmethod
    def _render(blocks: list[_Block]) -> str:
        ordered = arrange_edges_first(blocks, key=lambda b: b.rank)
        return "\n\n".join(block.render() for block in ordered)

    def _summarize(self, block: _Block) -> None:
        summary: str | None = None
        if self.summarizer is not None:
            try:
                summary = self._llm_summary(f"{block.name}/", block.body)
            except Exception as exc:  # noqa: BLE001 - packing must degrade, never crash the run
                tqdm.write(f"Could not summarize `{block.name}/` ({exc}); using a deterministic summary.")
                summary = None

        if summary:
            key_files = sorted(block.cards, key=lambda c: (-c.rank, c.path))[:_KEY_FILES_SHOWN]
            summary += "\nKey files: " + ", ".join(f"`{c.path}`" for c in key_files)
        else:
            summary = self._deterministic_summary(block)

        block.body = summary
        block.summarized = True
        block.refresh()

    def _llm_summary(self, label: str, text: str) -> str:
        summarizer = self.summarizer
        if summarizer is None:
            raise RuntimeError("No summarizer configured.")
        rounds = 0
        while TokenUtilities.estimate_tokens(text) > self.chunk_budget and rounds < self.max_rounds:
            chunks = self._split_lines(text, self.chunk_budget)
            if len(chunks) == 1:
                break
            parts = []
            for chunk in chunks:
                self.llm_calls += 1
                parts.append(summarizer(label, chunk).strip())
            text = "\n".join(parts)
            rounds += 1

        limit_chars = int(self.chunk_budget * TokenUtilities.CHARS_PER_TOKEN)
        if len(text) > limit_chars:
            text = text[:limit_chars]

        self.llm_calls += 1
        return summarizer(label, text).strip()

    @staticmethod
    def _split_lines(text: str, limit_tokens: int) -> list[str]:
        chunks: list[list[str]] = [[]]
        used = 0
        for line in text.splitlines():
            cost = TokenUtilities.estimate_tokens(line) + 1
            if chunks[-1] and used + cost > limit_tokens:
                chunks.append([])
                used = 0
            chunks[-1].append(line)
            used += cost
        return ["\n".join(chunk) for chunk in chunks if chunk]

    @staticmethod
    def _deterministic_summary(block: _Block) -> str:
        ordered = sorted(block.cards, key=lambda c: (-c.rank, c.path))
        lines = [
            f"- `{c.path}`: {c.summary}" if c.summary else f"- `{c.path}`"
            for c in ordered[:_KEY_FILES_SHOWN]
        ]
        others = ordered[_KEY_FILES_SHOWN:]
        if others:
            names = ", ".join(f"`{posixpath.basename(c.path)}`" for c in others[:_OTHER_FILES_SHOWN])
            more = len(others) - _OTHER_FILES_SHOWN
            lines.append("Other files: " + names + (f" (+{more} more)" if more > 0 else ""))
        return "\n".join(lines)

    @staticmethod
    def _lift(blocks: list[_Block]) -> list[_Block] | None:
        """Moves every block one directory level up, merging siblings. None if at the root."""
        if all(b.name == "." for b in blocks):
            return None

        groups: dict[str, list[_Block]] = defaultdict(list)
        for block in blocks:
            parent = "." if block.name == "." else (posixpath.dirname(block.name) or ".")
            groups[parent].append(block)

        lifted = []
        for parent, members in sorted(groups.items()):
            if len(members) == 1 and members[0].name == parent:
                lifted.append(members[0])
                continue
            body = "\n".join(f"{m.heading}\n{m.body}" for m in members)
            cards = [c for m in members for c in m.cards]
            only_summarized_single = len(members) == 1 and members[0].summarized
            lifted.append(_Block(parent, cards, body, summarized=only_summarized_single))
        return lifted

    def _hard_trim(self, blocks: list[_Block], budget: int) -> list[_Block]:
        """Last resort: drop the least important blocks, then truncate the last one."""
        ordered = sorted(blocks, key=lambda b: b.rank, reverse=True)
        while len(ordered) > 1 and self._total(ordered) > budget:
            ordered.pop()
        if ordered and self._total(ordered) > budget:
            only = ordered[0]
            allowed = max(int(budget * TokenUtilities.CHARS_PER_TOKEN) - len(only.heading) - 1, 80)
            only.body = only.body[:allowed].rstrip() + " …"
            only.refresh()
        return ordered
