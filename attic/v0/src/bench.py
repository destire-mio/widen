"""Measure memory side effects: answer the same questions with no memory, plain memory, and Widen.

For each question and arm: sample several answers, count how many distinct ideas they contain
(an LLM groups same-meaning ideas), and how far the ideas sit from the memories (novelty).
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from pathlib import Path

from .core import widen
from .similarity import novelty

ANSWER_SYSTEM = """Answer the user's question with {k} concrete ideas, one sentence each.
Write in the same language as the question.
Return JSON: {{"ideas": ["<idea>", ...]}}"""

MEMORY_BLOCK = "\n\nWhat you remember about the user:\n{memories}"

GROUP_SYSTEM = """You get a numbered list of ideas. Group ideas that say essentially the same thing.
Every number must appear in exactly one group.
Return JSON: {"groups": [[<numbers>], ...]}"""

ARMS = ("none", "memory", "widen")


@dataclass
class ArmScore:
    ideas: list[str] = field(default_factory=list)
    distinct: int = 0
    novelty: float = 0.0
    intents: list[str] = field(default_factory=list)


def plain_answer(question: str, memories: list[str] | None, llm, k: int = 5) -> list[str]:
    system = ANSWER_SYSTEM.format(k=k)
    if memories:
        system += MEMORY_BLOCK.format(memories="\n".join(f"- {m}" for m in memories))
    return [i for i in llm.json("answer", system, question, temperature=1.0).get("ideas", []) if isinstance(i, str)]


def count_distinct(ideas: list[str], llm) -> int:
    if len(ideas) < 2:
        return len(ideas)
    listing = "\n".join(f"{n}. {idea}" for n, idea in enumerate(ideas, 1))
    groups = llm.json("group", GROUP_SYSTEM, listing, temperature=0).get("groups", [])
    seen: set[int] = set()
    count = 0
    for group in groups:
        members = {i for i in group if isinstance(i, int) and 1 <= i <= len(ideas)} - seen
        if members:
            count += 1
            seen |= members
    return count + (len(ideas) - len(seen))  # ungrouped ideas count as their own group


def score_question(question: str, memories: list[str], llm, samples: int = 3, k: int = 5,
                   cache_dir: Path | None = None) -> dict[str, ArmScore]:
    scores = {arm: ArmScore() for arm in ARMS}
    for _ in range(samples):
        scores["none"].ideas += plain_answer(question, None, llm, k)
        scores["memory"].ideas += plain_answer(question, memories, llm, k)
        result = widen(question, memories, llm, k=k, cache_dir=cache_dir)
        scores["widen"].intents.append(result.intent)
        if result.intent == "explore":
            scores["widen"].ideas += [p.text for p in result.picks]
        else:  # plain task: Widen steps aside and behaves like plain memory
            scores["widen"].ideas += plain_answer(question, memories, llm, k)
    for score in scores.values():
        score.distinct = count_distinct(score.ideas, llm)
        score.novelty = round(statistics.mean(novelty(i, memories) for i in score.ideas), 3) if score.ideas else 0.0
    return scores


def run(questions: list[dict], memories: list[str], llm, samples: int = 3, k: int = 5,
        cache_dir: Path | None = None) -> list[dict]:
    rows = []
    for q in questions:
        scores = score_question(q["question"], memories, llm, samples, k, cache_dir)
        rows.append({"scenario": q.get("scenario", ""), "question": q["question"],
                     "scores": {arm: s.__dict__ for arm, s in scores.items()}})
    return rows


def report(rows: list[dict], samples: int) -> str:
    lines = [f"Samples per arm per question: {samples}. Distinct = idea groups after merging same-meaning ideas. "
             "Novelty = 1 - character similarity to the closest memory (higher = further from memory).", "",
             "| Scenario | Question | Widen intent | Distinct: none / memory / widen | Novelty: none / memory / widen |",
             "| --- | --- | --- | --- | --- |"]
    for row in rows:
        s = row["scores"]
        intents = ", ".join(sorted(set(s["widen"]["intents"])))
        lines.append(f"| {row['scenario']} | {row['question']} | {intents} | "
                     f"{s['none']['distinct']} / {s['memory']['distinct']} / {s['widen']['distinct']} | "
                     f"{s['none']['novelty']} / {s['memory']['novelty']} / {s['widen']['novelty']} |")
    return "\n".join(lines) + "\n"


def load_questions(path: str | Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
