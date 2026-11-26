"""A per-user list of hard limits, distilled once from all memories and cached.

Bench v2 showed the filter missed most unfit directions because what it was given was noise: the first 12
"constraint/dislike" memories were one-off trivia ("C drive almost full", "sore throat"), real limits
("wrist tendinitis, 4 hours of drawing a day", "doesn't like phone calls") were cut off, and abilities
("can't read long text", "can't use complex phone apps") were tagged as background, so they never reached it.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .clean import Tagged

LIMITS_SYSTEM = """You read everything an AI assistant remembers about one user and list the HARD LIMITS that would
make a suggestion impossible or unwelcome for them. Only lasting limits, not one-off situations
(a cold this week, a full disk, one late delivery are not limits). Kinds:
body (health, injury, energy) | time (when they are free, how much) | money | ability (what they cannot do or
handle, e.g. reading long text, using complex apps, a skill they lack) | dislike (what they avoid) | place (where
they live or can go, living situation).
If something changed over time, keep the latest state. At most 12 items, most important first, each one short line.
Write the items in the same language as most memories.
Return JSON: {"limits": [{"kind": "<kind>", "limit": "<short line>"}]}"""


def distill_limits(tagged: list[Tagged], llm, cache_path: Path | None = None) -> list[str]:
    memories = [t.memory for t in tagged]
    if not memories:
        return []
    key = hashlib.sha256("\n".join(sorted(memories)).encode()).hexdigest()[:16]
    cache: dict = {}
    if cache_path and cache_path.is_file():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        if key in cache:
            return cache[key]
    listing = "\n".join(f"- ({t.kind}) {t.memory}" for t in tagged)
    try:
        out = llm.json("limits", LIMITS_SYSTEM, listing, temperature=0).get("limits", [])
    except Exception:  # without limits we still answer; the fine rank and checks just see "nothing known"
        return []
    limits = [f"({x.get('kind', '?')}) {x['limit']}" for x in out if isinstance(x, dict) and x.get("limit")][:12]
    if cache_path:
        cache[key] = limits
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return limits
