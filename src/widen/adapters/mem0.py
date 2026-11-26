"""WidenMemory: wrap a Mem0 Memory so search() adds the fourth (exploration) path.

    from mem0 import Memory
    from widen.adapters.mem0 import WidenMemory
    memory = WidenMemory(Memory.from_config(cfg))
    memory.search("周末做点什么？", filters={"user_id": "ma"}, top_k=10)

Plain questions return exactly what Mem0 returns. Idea requests return Mem0's format with exploration directions
only (fit was already checked against the user's hard limits inside the plugin); handing the answering model the
memories as well pulled a third of its ideas back to them (benchmark arms E2 vs E3). No instructions are added.
include_memories=True also returns the cleaned memories (one per topic, tagged with their kind).
Every other method (add, get_all, delete, ...) is passed through to Mem0 untouched.
"""
from __future__ import annotations

import random
from pathlib import Path

from ..core.pipeline import CACHE_DIR, Table, widen


class WidenMemory:
    def __init__(self, mem0, llm=None, *, table: Table | None = None, level: int = 4, seed: int | None = None,
                 cache_dir: Path = CACHE_DIR, directions: int = 4, max_memories: int = 5,
                 include_memories: bool = False, lam: float = 1.0):
        if llm is None:
            from ..llm import LLM
            llm = LLM()
        self.mem0, self.llm = mem0, llm
        self.table = table or Table(level)
        self.rng = random.Random(seed)
        self.cache_dir, self.directions, self.max_memories = cache_dir, directions, max_memories
        self.include_memories, self.lam = include_memories, lam
        self.last = None  # the last WidenOutput, for inspection

    def __getattr__(self, name):
        return getattr(self.mem0, name)

    def search(self, query: str, *, filters: dict | None = None, top_k: int = 10, context: str = "", **kwargs):
        from ..core.intent import judge_intent_queries
        intent, reason, queries = judge_intent_queries(query, self.llm, context)
        if intent == "do":
            self.last = None
            return self.mem0.search(query, filters=filters, top_k=top_k, **kwargs)
        found = self.mem0.search(query, filters=filters, top_k=top_k * 3, **kwargs)
        retrieved = [r["memory"] for r in found.get("results", []) if r.get("memory")]
        everything = self.mem0.get_all(filters=filters, top_k=10000)
        all_memories = [r["memory"] for r in everything.get("results", []) if r.get("memory")]
        out = widen(query, retrieved, all_memories, self.llm, self.table, rng=self.rng, cache_dir=self.cache_dir,
                    max_memories=self.max_memories, directions=self.directions, intent=intent, queries=queries,
                    lam=self.lam)
        out.reason = reason
        self.last = out
        by_text = {r["memory"]: r for r in found.get("results", [])}
        results = []
        for t in (out.memories if self.include_memories else []):
            r = dict(by_text.get(t.memory, {"memory": t.memory}))
            r["metadata"] = {**(r.get("metadata") or {}), "widen": "memory", "kind": t.kind}
            results.append(r)
        for d in out.directions:
            results.append({"memory": d.text, "score": None,
                            "metadata": {"widen": "explore", "slot": d.slot, "topic": d.title, "topic_zh": d.zh}})
        return {"results": results}
