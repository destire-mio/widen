"""The whole Widen pass, independent of any memory store.

widen(query, retrieved, all_memories, llm, table) -> WidenOutput
  retrieved     memories the store found for this query, best first (Mem0's three paths)
  all_memories  every memory of this user (to light the table; tags and lights are cached)

intent + search phrases -> clean -> light -> recall by the QUESTION -> coarse rank -> fine rank + hard-limit filter
-> rerank -> bridge. Model calls per idea request: intent (+ phrases), fine, bridge (+ tags / lights for memories
seen for the first time).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path

from .clean import Tagged, clean
from .explore import Direction, bridge
from .intent import judge_intent_queries
from .light import light
from .limits import distill_limits
from .neighbors import Neighbors
from .rank import Scored, coarse, fine, interests, recall, rerank

CACHE_DIR = Path.home() / ".cache" / "widen"


@dataclass
class WidenOutput:
    intent: str
    reason: str = ""
    memories: list[Tagged] = field(default_factory=list)      # cleaned, one per topic
    directions: list[Direction] = field(default_factory=list)
    candidates: list[Scored] = field(default_factory=list)     # after the fine rank, for inspection
    queries: list[str] = field(default_factory=list)          # search phrases the question was turned into
    limits: list[str] = field(default_factory=list)           # the user's distilled hard limits


class Table:
    """The topic table (Wikipedia vital articles) plus its neighbour index. Load once, reuse."""

    def __init__(self, level: int = 4):
        from ..table.vital import load
        self.level = level
        self.rows, vectors = load(level)
        self.neighbors = Neighbors(self.rows, vectors)
        self.walker = None
        try:  # the clickstream graph is optional; without it candidates come from the section tree + vectors
            from .walk import ClickWalk
            self.walker = ClickWalk(self.neighbors, level)
        except FileNotFoundError:
            pass


def widen(query: str, retrieved: list[str], all_memories: list[str], llm, table: Table, *,
          rng: random.Random | None = None, cache_dir: Path = CACHE_DIR, max_memories: int = 5,
          directions: int = 4, intent: str | None = None, queries: list[str] | None = None, context: str = "",
          lam: float = 0.5, coarse_k: int = 80) -> WidenOutput:
    reason = "given"
    if intent is None or queries is None:
        judged, reason, phrases = judge_intent_queries(query, llm, context)
        intent = intent or judged
        queries = queries if queries is not None else phrases
    out = WidenOutput(intent, reason, queries=list(queries))
    if intent == "do":
        return out
    rng = rng or random.Random()
    tag_cache = cache_dir / "tags.json"
    out.memories = clean(retrieved, llm, tag_cache)[:max_memories]
    everyone = clean(all_memories, llm, tag_cache)
    lit = light([t.memory for t in everyone], table.rows, llm, cache_dir / f"light-l{table.level}.json")
    nb = table.neighbors
    inter, lit_all = interests(lit, everyone)
    pool, feats = recall(queries, lit_all, nb, table.walker)
    explore = intent == "explore"   # "alternatives": stay close, no exploration slot
    cands = coarse(pool, inter, lit_all, nb, feats, lam=lam if explore else 0.0, k=coarse_k)
    limits = distill_limits(everyone, llm, cache_dir / "limits.json")   # once per user, cached
    out.limits = limits
    out.candidates = fine(query, cands, everyone, nb, llm, rng, limits=limits)
    chosen = rerank(out.candidates, nb, n=directions, spares=3)
    if not explore:
        chosen = [s for s in chosen if s.slot == "ranked"]
    out.directions = bridge(query, chosen, everyone, nb, llm, limits=limits, n=directions)
    if not explore:
        out.directions = [d for d in out.directions if d.slot == "ranked"][:directions]
    return out
