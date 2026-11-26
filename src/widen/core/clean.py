"""Step 2: keep only memories about the person, tag what kind they are, and merge ones that say the same thing.

The benchmark found more than half of Mem0's memories are the assistant's own advice or one-off questions, and 17%
of ideas built on them; and a fact mentioned 4 times pulled ~6x more ideas than one mentioned once.
Tags are cached by memory text.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

KINDS = ("like", "skill", "resource", "constraint", "dislike", "background")

CLEAN_SYSTEM = """You get things an AI assistant remembers about one user. For each numbered memory decide:
- "about": true if it states something about the user themself (what they like, can do, have, cannot do, avoid, or who they are).
  false if it is mainly advice or text the assistant gave, a one-off question the user asked, or small talk.
- "kind": like (enjoys it; liking is not skill) | skill (can do it, experience, job) | resource (has access to people, data, places, tools)
  | constraint (limits of time, money, body, place) | dislike (avoids it) | background (age, home, family, pets).
- "topic": 2-5 lowercase English words naming the underlying fact, identical for memories that say the same thing
  (e.g. "makes hand-pulled noodles" for every memory about their noodle-making).
Return JSON: {"tags": [{"memory": <n>, "about": true|false, "kind": "<kind>", "topic": "<words>"}]}"""


@dataclass
class Tagged:
    memory: str
    kind: str
    topic: str


def _key(memory: str) -> str:
    return hashlib.sha256(memory.encode()).hexdigest()[:16]


def tag(memories: list[str], llm, cache_path: Path | None = None, batch: int = 25) -> dict[str, dict | None]:
    cache: dict[str, dict | None] = {}
    if cache_path and cache_path.is_file():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    todo = [m for m in dict.fromkeys(memories) if _key(m) not in cache]
    for lo in range(0, len(todo), batch):
        chunk = todo[lo:lo + batch]
        listing = "\n".join(f"{n}. {m}" for n, m in enumerate(chunk, 1))
        for t in llm.json("clean", CLEAN_SYSTEM, listing, temperature=0).get("tags", []):
            n = t.get("memory")
            if isinstance(n, int) and 1 <= n <= len(chunk):
                ok = t.get("about") is True and t.get("kind") in KINDS
                cache[_key(chunk[n - 1])] = {"kind": t["kind"], "topic": str(t.get("topic", "")).strip().lower()} if ok else None
    if cache_path and todo:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return {m: cache.get(_key(m)) for m in memories}


def clean(memories: list[str], llm, cache_path: Path | None = None) -> list[Tagged]:
    """About-the-person memories only, one per topic (the first one seen wins, so pass them best-first)."""
    tags = tag(memories, llm, cache_path)
    seen, out = set(), []
    for m in memories:
        t = tags.get(m)
        if not t:
            continue
        topic = t["topic"] or m.lower()
        if topic in seen:
            continue
        seen.add(topic)
        out.append(Tagged(m, t["kind"], topic))
    return out
