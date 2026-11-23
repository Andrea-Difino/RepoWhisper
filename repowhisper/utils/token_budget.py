import math
from collections.abc import Callable
from typing import ClassVar


class TokenUtilities:

    DEFAULT_CONTEXT_BUDGET: ClassVar[int] = 6000
    # chars-per-token ratio
    CHARS_PER_TOKEN: ClassVar[float] = 3.5

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """
        Cheap, dependency-free, model-agnostic token estimate.

        Args:
            text (str): text to measure.

        Returns:
            int: estimated number of tokens (0 for an empty string).
        """
        if not text:
            return 0
        return math.ceil(len(text) / cls.CHARS_PER_TOKEN)


type ImportanceScorer[T] = Callable[[T], float]

def arrange_edges_first[T](items: list[T], key: ImportanceScorer[T]) -> list[T]:
    """
    Reorder items so the most important ones sit at the START and at the END of the
    list while the least important end up in the middle. (prevent "lost in the middle" effect)

    Args:
        items (list): items to reorder.
        key (ImportanceScorer): Function returning the importance of an item (higher = more important).

    Returns:
        list: the reordered list (a new list, the input is not modified).
    """
    ranked = sorted(items, key=key, reverse=True)
    return ranked[0::2] + ranked[1::2][::-1]
