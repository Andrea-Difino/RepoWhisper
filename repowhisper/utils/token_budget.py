import math
from collections.abc import Callable
from typing import ClassVar


class TokenUtilities:

    # Default number of tokens reserved for the *evidence* (facts + module notes + tree)
    # that is handed to the Architect and the Storyteller. 
    DEFAULT_CONTEXT_BUDGET: ClassVar[int] = 6000

    # Conservative chars-per-token ratio for mixed code/prose
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


def arrange_edges_first(items: list, key: Callable[[object], float]) -> list:
    """
    Reorder items so the most important ones sit at the START and at the END of the
    list while the least important end up in the middle.

    LLMs use information at the beginning and at the end of a long prompt better than
    information in the middle ("lost in the middle"), so this is applied to the order
    in which evidence is placed in a prompt.

    Args:
        items (list): items to reorder.
        key: Function returning the importance of an item (higher = more important).

    Returns:
        list: the reordered list (a new list, the input is not modified).
    """
    ranked = sorted(items, key=key, reverse=True)
    return ranked[0::2] + ranked[1::2][::-1]
