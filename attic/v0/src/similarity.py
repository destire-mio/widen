"""Text similarity from character 2- and 3-grams. No model download; works for Chinese and English.

Swap in an embedding model later by replacing `similarity`.
"""
from __future__ import annotations

import math
import re
from collections import Counter


def _grams(text: str) -> Counter:
    text = re.sub(r"\s+", " ", text.lower()).strip()
    grams: Counter = Counter()
    for n in (2, 3):
        for i in range(len(text) - n + 1):
            grams[text[i:i + n]] += 1
    return grams


def similarity(a: str, b: str) -> float:
    ga, gb = _grams(a), _grams(b)
    if not ga or not gb:
        return 0.0
    dot = sum(count * gb[g] for g, count in ga.items())
    return dot / (math.sqrt(sum(v * v for v in ga.values())) * math.sqrt(sum(v * v for v in gb.values())))


def novelty(text: str, memories: list[str]) -> float:
    """1 - similarity to the closest memory. 1.0 = shares nothing with any memory."""
    if not memories:
        return 1.0
    return 1.0 - max(similarity(text, m) for m in memories)
