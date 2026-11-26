"""Step 5, candidates: from a lit article, find 'adjacent' and 'far' articles.

Distance comes from Wikipedia's own section tree (like Google's 4-level cluster tree); vectors only rank inside a
band. Pure vectors drifted to surface features (Xiangqi -> "Communist Party" via "Chinese", CSS -> "French" via
"language"), because article descriptions are only a few words.

  same leaf section        -> too close (a sibling of the same kind: Xiangqi -> Mahjong), skipped
  shares >= 1 tree level   -> adjacent, ranked by corrected vector similarity
  shares nothing           -> far, sampled at random from the middle of the similarity ranking
"""
from __future__ import annotations

import random

import numpy as np

# Never offered as a random "far" direction (a user's own memory may still light them, and their neighbours stay).
FAR_BLOCKED = (
    "Philosophy and religion / Religion and spirituality",
    "Everyday life / Sexuality and gender",
    "Society and social sciences / Law / Crime",
    "Society and social sciences / Politics and government",
    "Society and social sciences / War and military",
    "Technology / Military technology",
    "Biology and health sciences / Health, medicine and disease / Morbidity",
    "Biology and health sciences / Health, medicine and disease / Drugs and pharmacology",
)


class Neighbors:
    def __init__(self, rows: list[dict], vectors: np.ndarray, hub_k: int = 10):
        self.rows = rows
        self.path = [r["section"].split(" / ") for r in rows]
        self.mean = vectors.mean(0)
        c = vectors - self.mean                             # centering: spreads similarities apart
        self.c = c / np.linalg.norm(c, axis=1, keepdims=True)
        self.hub_k = hub_k
        self._rt = None

    def _hubness(self) -> np.ndarray:
        """Mean similarity to each article's k nearest neighbours (CSLS term); computed once in blocks."""
        if self._rt is None:
            rt = np.empty(len(self.rows), dtype=np.float32)
            for lo in range(0, len(self.rows), 1024):
                block = self.c[lo:lo + 1024] @ self.c.T
                rt[lo:lo + 1024] = np.sort(block, 1)[:, -self.hub_k - 1:-1].mean(1)
            self._rt = rt
        return self._rt

    def scores(self, i: int) -> np.ndarray:
        """CSLS: similarity minus how 'similar to everything' each side is."""
        rt = self._hubness()
        return 2 * (self.c @ self.c[i]) - rt[i] - rt

    def shared(self, i: int, j: int) -> int:
        n = 0
        for a, b in zip(self.path[i], self.path[j]):
            if a != b:
                break
            n += 1
        return n

    def adjacent(self, i: int, k: int = 5, exclude: set[int] = frozenset(), prefer_depth: int = 2) -> list[int]:
        """Closest articles that share part of the section path but not the leaf; deeper shared path first
        (same subsection before same top section, so Xiangqi gets martial arts before soy sauce)."""
        s = self.scores(i)
        leaf = len(self.path[i])
        tiers: dict[int, list[int]] = {}
        for j in np.argsort(-s):
            j = int(j)
            if j == i or j in exclude:
                continue
            depth = self.shared(i, j)
            if depth >= 1 and not (depth == leaf == len(self.path[j])):
                tiers.setdefault(min(depth, prefer_depth), []).append(j)
        out: list[int] = []
        for depth in sorted(tiers, reverse=True):
            out += tiers[depth][: k - len(out)]
            if len(out) == k:
                break
        return out

    def far(self, i: int, k: int = 3, rng: random.Random | None = None, exclude: set[int] = frozenset()) -> list[int]:
        """A random *other* top-level section first (so big sections like biology don't dominate), then an
        article from the middle third of that section's ranking (the very bottom is planets and metals)."""
        rng = rng or random.Random()
        s = self.scores(i)
        tops: dict[str, list[int]] = {}
        for j in np.argsort(-s):
            j = int(j)
            if self.shared(i, j) == 0 and j not in exclude and not self.rows[j]["section"].startswith(FAR_BLOCKED):
                tops.setdefault(self.path[j][0], []).append(j)
        out = []
        for top in rng.sample(sorted(tops), min(k, len(tops))):
            order = tops[top]
            third = len(order) // 3
            out.append(rng.choice(order[third:2 * third] or order))
        return out
