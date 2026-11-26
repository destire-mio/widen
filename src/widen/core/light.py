"""Step 3, light up: map each (cleaned) memory to one topic-table article.

Vectors failed here (Mem0 memories are English mixed with Chinese, descriptions are short: "面馆" -> "potato"),
so an LLM picks in two rounds: first a subsection (~74), then an article inside it. Each memory is mapped once
and cached by its text, since memories change slowly.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

SECTION_SYSTEM = """You map things an assistant remembers about a user onto a topic list.
For each numbered memory, pick the ONE section whose topics best cover what the memory is about
(the activity, skill, object or field itself, not the fact that the user talked about it).
If the memory is about nothing a topic list could cover (pure small talk, scheduling), answer 0.
Return JSON: {"picks": [{"memory": <n>, "section": <section number or 0>}]}"""

ARTICLE_SYSTEM = """You map things an assistant remembers about a user onto encyclopedia articles.
For each numbered memory, pick the ONE article from the list that best names what the memory is about.
Prefer the most specific article that still fits. If none fits, answer 0.
Return JSON: {"picks": [{"memory": <n>, "article": <article number or 0>}]}"""


@dataclass
class Lit:
    memory: str
    article: int | None   # row index in the topic table, None if nothing fits
    title: str = ""
    zh: str = ""


def section_key(row: dict, depth: int = 2) -> str:
    return " / ".join(row["section"].split(" / ")[:depth])


def _numbered(items: list[str]) -> str:
    return "\n".join(f"{n}. {x}" for n, x in enumerate(items, 1))


def light(memories: list[str], rows: list[dict], llm, cache_path: Path | None = None, batch: int = 20) -> list[Lit]:
    cache: dict[str, int | None] = {}
    if cache_path and cache_path.is_file():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    key = lambda m: hashlib.sha256(m.encode()).hexdigest()[:16]
    todo = [m for m in dict.fromkeys(memories) if key(m) not in cache]

    sections = sorted({section_key(r) for r in rows})
    members = defaultdict(list)
    for i, r in enumerate(rows):
        members[section_key(r)].append(i)

    # round 1: memory -> section
    chosen: dict[str, str] = {}
    for lo in range(0, len(todo), batch):
        chunk = todo[lo:lo + batch]
        user = f"Sections:\n{_numbered(sections)}\n\nMemories:\n{_numbered(chunk)}"
        for p in llm.json("light-section", SECTION_SYSTEM, user, temperature=0).get("picks", []):
            m, s = p.get("memory"), p.get("section")
            if isinstance(m, int) and 1 <= m <= len(chunk):
                if isinstance(s, int) and 1 <= s <= len(sections):
                    chosen[chunk[m - 1]] = sections[s - 1]
                else:
                    cache[key(chunk[m - 1])] = None

    # round 2: memory -> article, one call per section (and per batch)
    by_section = defaultdict(list)
    for m, s in chosen.items():
        by_section[s].append(m)
    for s, mems in by_section.items():
        ids = members[s]
        listing = _numbered([f"{rows[i]['title']} ({rows[i]['zh']}): {rows[i]['lead']}" for i in ids])
        for lo in range(0, len(mems), batch):
            chunk = mems[lo:lo + batch]
            user = f"Articles:\n{listing}\n\nMemories:\n{_numbered(chunk)}"
            for p in llm.json("light-article", ARTICLE_SYSTEM, user, temperature=0).get("picks", []):
                m, a = p.get("memory"), p.get("article")
                if isinstance(m, int) and 1 <= m <= len(chunk):
                    cache[key(chunk[m - 1])] = ids[a - 1] if isinstance(a, int) and 1 <= a <= len(ids) else None

    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    out = []
    for m in memories:
        idx = cache.get(key(m))
        out.append(Lit(m, idx, rows[idx]["title"] if idx is not None else "", rows[idx]["zh"] if idx is not None else ""))
    return out
