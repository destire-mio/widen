"""Last step of the fourth path: turn the chosen topics into one concrete direction each, for this question.

The bridge sees only short labels of the user's limits and dislikes, never skills, resources or full memory
sentences: given "noodle shop" and "Sichuan pepper" (or a limit like "no time, Monday is noodle practice"),
earlier versions turned every topic back into noodle-shop ideas. Whether the person can use a topic was already
decided by the fine rank.
"""
from __future__ import annotations

from dataclasses import dataclass

from .clean import Tagged
from .neighbors import Neighbors
from .rank import LIMIT_KINDS, Scored

BRIDGE_SYSTEM = """You help a user who asked an open question by suggesting directions they have not explored.
You get the question, the user's hard limits, and numbered topics chosen for them.
For EACH topic:
1. write one concrete direction in one sentence that answers THIS question, built from the topic itself;
2. then check the sentence you wrote against every hard limit (body, time, money, ability, dislike, place) and
   against the question itself: "ok": false if any limit makes it infeasible or unwelcome, or if it does not
   really answer the question; give a short "reason" when false.
Quietly respect the limits in the wording: only mention a limit when the direction is specifically shaped by it.
Do not mention the topic list or why it was chosen. Write in the same language as the question.
Return JSON: {"directions": [{"id": "<T1...>", "direction": "<one sentence>", "ok": true|false, "reason": "<short>"}]}"""


@dataclass
class Direction:
    text: str
    article: int
    title: str
    zh: str
    slot: str           # "ranked" or "explore"
    score: float | None = None
    novelty: float = 0.0
    ok: bool = True
    reason: str = ""


def bridge(question: str, chosen: list[Scored], tagged: list[Tagged], nb: Neighbors, llm,
           limits: list[str] | None = None, n: int | None = None) -> list[Direction]:
    """Write a direction per topic and check it against the hard limits in the same call (the final filter:
    a fine topic like "community" can still become "call your neighbours every day" for someone who hates
    phone calls). With n, keep n passing directions: n-1 ranked and one explore when one passes."""
    if not chosen:
        return []
    if limits is None:
        limits = []
        for t in tagged:
            if t.kind in LIMIT_KINDS and t.topic and t.topic not in limits:
                limits.append(t.topic)
        limits = limits[:10]
    facts = [f"- {x}" for x in limits] or ["- (nothing known)"]
    rows = nb.rows
    ids = {f"T{k}": s for k, s in enumerate(chosen, 1)}
    listing = "\n".join(f"{k}. {rows[s.article]['title']} ({rows[s.article]['zh']}): {rows[s.article]['lead']}"
                        for k, s in ids.items())
    system = BRIDGE_SYSTEM
    if any("\u4e00" <= ch <= "\u9fff" for ch in question):
        system += "\nThe question is in Chinese: write every direction in Simplified Chinese."
    user = f"Question: {question}\n\nHard limits:\n" + "\n".join(facts) + f"\n\nTopics:\n{listing}"
    out = []
    for d in llm.json("bridge", system, user, temperature=0.7).get("directions", []):
        s = ids.get(str(d.get("id", "")).strip().upper())
        if s is not None and d.get("direction"):
            r = rows[s.article]
            out.append(Direction(d["direction"], s.article, r["title"], r["zh"], s.slot, s.fine, s.novelty,
                                 d.get("ok") is not False, str(d.get("reason") or "")))
    order = {id(s): k for k, s in enumerate(chosen)}
    out.sort(key=lambda d: next((order[id(s)] for s in chosen if s.article == d.article), 0))
    if n is None:
        return [d for d in out if d.ok]
    passed = [d for d in out if d.ok]
    ranked = [d for d in passed if d.slot == "ranked"][: n - 1]
    explore = [d for d in passed if d.slot == "explore"][:1]
    keep = ranked + explore
    for d in passed:
        if len(keep) >= n:
            break
        if d not in keep:
            keep.append(d)
    return keep[:n]
