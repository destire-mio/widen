"""Claude Code UserPromptSubmit hook.

Plain tasks pass through untouched. Requests for new ideas get extra context: what memory already
covers, which neighbouring areas are unexplored, and the rule that memory checks fit but does not
choose the direction. Any failure prints nothing, so the hook can never block a prompt.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .core import dark_topics, judge_intent, light_topics
from .memory import load_memories

FORCE_PREFIXES = ("/widen", "widen:")
CACHE_DIR = Path.home() / ".cache" / "widen"


def memory_dir(event: dict) -> Path | None:
    if os.getenv("WIDEN_MEMORY"):
        return Path(os.environ["WIDEN_MEMORY"]).expanduser()
    transcript = event.get("transcript_path")
    if transcript:  # ~/.claude/projects/<project>/<session>.jsonl -> <project>/memory
        candidate = Path(transcript).expanduser().parent / "memory"
        if candidate.is_dir():
            return candidate
    return None


def build_context(question: str, lit: list[dict], dark: list[dict]) -> str:
    lit_text = "; ".join(f"{t.get('name')} ({t.get('kind')})" for t in lit) or "nothing yet"
    dark_text = "; ".join(t.get("name", "") for t in dark)
    return (
        "[Widen] The user is asking for new ideas, not a fixed task.\n"
        f"Your memory of the user only covers: {lit_text}.\n"
        "That memory is incomplete, and liking something is not the same as knowing it.\n"
        f"Unexplored areas next to it: {dark_text}.\n"
        "Rules: at least half of your suggestions must come from the unexplored areas, not from what memory already shows. "
        "Use memory only to check whether a suggestion fits the user, never to pick the direction. "
        "After each suggestion, note in brackets which memory it relies on, or 'no memory used'."
    )


def handle(event: dict, llm) -> dict | None:
    prompt = (event.get("prompt") or "").strip()
    forced = prompt.lower().startswith(FORCE_PREFIXES)
    if forced:
        question = prompt.split(None, 1)[1] if " " in prompt else prompt
    else:
        question = prompt
        if judge_intent(question, llm)[0] != "explore":
            return None
    folder = memory_dir(event)
    memories = load_memories(folder) if folder else []
    lit = light_topics(memories, llm, CACHE_DIR)
    dark = dark_topics(question, lit, llm)
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                   "additionalContext": build_context(question, lit, dark)}}


def main(stdin_text: str, llm_factory) -> str:
    try:
        output = handle(json.loads(stdin_text or "{}"), llm_factory())
    except Exception:
        return ""
    return json.dumps(output, ensure_ascii=False) if output else ""
