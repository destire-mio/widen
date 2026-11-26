"""The Widen pipeline: judge intent, light up known topics, explore the dark ones, filter, judge fit."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .similarity import novelty

LANG = "Write every text field in the same language as the user's question."

INTENT_SYSTEM = """You classify one message a user sent to an AI assistant.
"do": a task with a clear target, a question with one right answer, or continuing existing work. The answer should stay close to what the user said.
"explore": the user wants new options, ideas or directions they may not have considered (brainstorming, what to learn or read next, alternative approaches).
If unsure, choose "do".
Return JSON: {"intent": "do" | "explore", "reason": "<one short sentence>"}"""

LIGHT_SYSTEM = """You read what an assistant remembers about a user and list the topics these memories touch.
Tag each topic with what the memory actually shows:
"like" = enjoys or prefers it, "know" = has skill or experience in it, "have" = has resources, access or people for it, "dislike" = avoids it.
Liking something is not knowing it: only tag "know" when the memory shows skill or experience.
Return JSON: {"topics": [{"name": "<short topic>", "kind": "like" | "know" | "have" | "dislike"}]}"""

DARK_SYSTEM = """You get a question and the topics a user is already known to touch (lit topics).
List topics relevant to the question that are NOT among the lit topics, but sit next to them: one step away, so the user could plausibly reach them.
Prefer steps away from "know" and "have" topics over steps away from "like" topics. Never step toward "dislike" topics.
Cover different directions; do not cluster around one lit topic.
""" + LANG + """
Return JSON: {"topics": [{"name": "<topic>", "near": "<the lit topic it neighbours>"}]}"""

EXPLORER_SYSTEM = """You are the explorer. You do not know this user. You only get a question and some unexplored areas.
Write distinct candidate answers to the question, each drawing on one of the areas. Spread them across the areas.
Each candidate is one concrete sentence, not a category.
""" + LANG + """
Return JSON: {"ideas": [{"text": "<one concrete sentence>", "area": "<area used>"}]}"""

JUDGE_SYSTEM = """You are the judge. You know what an assistant remembers about the user.
Pick the candidates that fit this user: plausible given their skills, resources and constraints.
Do NOT prefer a candidate because it resembles their past. Fit means "could work for them", not "like what they did before".
For each pick, say in one short line why it fits, and quote the single memory you relied on, or null if none.
""" + LANG + """
Return JSON: {"picks": [{"index": <candidate number>, "fit": "<one line>", "memory": "<quoted memory or null>"}]}"""


@dataclass
class Idea:
    text: str
    area: str = ""
    novelty: float = 0.0
    fit: str = ""
    memory: str | None = None


@dataclass
class WidenResult:
    question: str
    intent: str
    intent_reason: str = ""
    lit: list[dict] = field(default_factory=list)
    dark: list[dict] = field(default_factory=list)
    candidates: list[Idea] = field(default_factory=list)
    picks: list[Idea] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) or "(none)"


def judge_intent(question: str, llm) -> tuple[str, str]:
    try:
        out = llm.json("intent", INTENT_SYSTEM, question, temperature=0)
    except Exception as exc:  # any failure -> do not explore
        return "do", f"intent check failed: {exc}"
    intent = out.get("intent")
    return (intent if intent in ("do", "explore") else "do"), out.get("reason", "")


def light_topics(memories: list[str], llm, cache_dir: Path | None = None) -> list[dict]:
    """Topics the memories touch. Cached by memory content, since memories change slowly."""
    if not memories:
        return []
    cache = None
    if cache_dir:
        digest = hashlib.sha256("\n".join(memories).encode()).hexdigest()[:16]
        cache = Path(cache_dir) / f"lit-{digest}.json"
        if cache.is_file():
            return json.loads(cache.read_text(encoding="utf-8"))
    topics = llm.json("light", LIGHT_SYSTEM, _bullets(memories), temperature=0).get("topics", [])
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(topics, ensure_ascii=False, indent=1), encoding="utf-8")
    return topics


def dark_topics(question: str, lit: list[dict], llm, n: int = 8) -> list[dict]:
    lit_lines = [f"{t.get('name')} ({t.get('kind')})" for t in lit]
    user = f"Question: {question}\n\nLit topics:\n{_bullets(lit_lines)}\n\nList {n} topics."
    return llm.json("dark", DARK_SYSTEM, user).get("topics", [])[:n]


def explore(question: str, dark: list[dict], llm, n: int = 12) -> list[Idea]:
    areas = [t.get("name", "") for t in dark]
    user = f"Question: {question}\n\nUnexplored areas:\n{_bullets(areas)}\n\nWrite {n} candidates."
    ideas = llm.json("explore", EXPLORER_SYSTEM, user, temperature=1.0).get("ideas", [])
    return [Idea(text=i["text"], area=i.get("area", "")) for i in ideas if i.get("text")]


def judge(question: str, candidates: list[Idea], memories: list[str], llm, k: int = 5) -> list[Idea]:
    listing = "\n".join(f"{n}. {c.text}" for n, c in enumerate(candidates, 1))
    user = (f"Question: {question}\n\nWhat you remember about the user:\n{_bullets(memories)}"
            f"\n\nCandidates:\n{listing}\n\nPick up to {k}.")
    picks = []
    for p in llm.json("judge", JUDGE_SYSTEM, user, temperature=0).get("picks", []):
        idx = p.get("index")
        if isinstance(idx, int) and 1 <= idx <= len(candidates) and candidates[idx - 1] not in picks:
            idea = candidates[idx - 1]
            idea.fit, idea.memory = p.get("fit", ""), p.get("memory") or None
            picks.append(idea)
    return picks[:k]


def widen(question: str, memories: list[str], llm, *, force: bool = False, n: int = 12, k: int = 5,
          min_novelty: float = 0.8, cache_dir: Path | None = None) -> WidenResult:
    """Run the whole pipeline. Returns early with intent "do" when the question is a plain task."""
    if force:
        intent, reason = "explore", "forced"
    else:
        intent, reason = judge_intent(question, llm)
    result = WidenResult(question=question, intent=intent, intent_reason=reason)
    if intent != "explore":
        return result
    result.lit = light_topics(memories, llm, cache_dir)
    result.dark = dark_topics(question, result.lit, llm)
    candidates = explore(question, result.dark, llm, n)
    for c in candidates:
        c.novelty = round(novelty(c.text, memories), 3)
    # Novelty filter: drop candidates too close to memory, but keep at least k to judge.
    far = [c for c in candidates if c.novelty >= min_novelty]
    if len(far) < k:
        far = sorted(candidates, key=lambda c: c.novelty, reverse=True)[:k]
    result.candidates = candidates
    result.picks = judge(question, far, memories, llm, k)
    return result
