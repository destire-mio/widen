"""Step 0: does the user want new ideas? do / alternatives / explore. Unsure or any error -> do."""
from __future__ import annotations

LEVELS = ("do", "alternatives", "explore")

INTENT_SYSTEM = """You classify the latest message a user sent to an AI assistant.
"do": a task with a clear target, a factual question, or continuing existing work. Recalling facts about the user or the past is "do".
"alternatives": the user wants a few other options inside a scope they already set (e.g. "besides X, what else for Y?").
"explore": the user wants open-ended new ideas or directions (brainstorming, what to learn, what to build, what to do next).
If unsure, choose "do".
Return JSON: {"intent": "do" | "alternatives" | "explore", "reason": "<one short sentence>"}"""


def judge_intent(query: str, llm, context: str = "") -> tuple[str, str]:
    user = f"Earlier in the conversation:\n{context}\n\nLatest message:\n{query}" if context else query
    try:
        out = llm.json("intent", INTENT_SYSTEM, user, temperature=0)
    except Exception as exc:  # never block the user's request
        return "do", f"intent check failed: {exc}"
    intent = out.get("intent")
    return (intent if intent in LEVELS else "do"), out.get("reason", "")


QUERY_SYSTEM = """You classify the latest message a user sent to an AI assistant, and if it asks for ideas, describe
where answers could come from.
"do": a task with a clear target, a factual question, or continuing existing work. Recalling facts about the user or the past is "do".
"alternatives": the user wants a few other options inside a scope they already set (e.g. "besides X, what else for Y?").
"explore": the user wants open-ended new ideas or directions (brainstorming, what to learn, what to build, what to do next).
If unsure, choose "do".
For "alternatives" or "explore", also give 6 short English search phrases (2-4 words each) naming DIFFERENT kinds
of topics a good answer to this question could draw on, the way an encyclopedia would name them
(e.g. for "what to do this weekend": "home cooking", "hiking", "woodworking", "board games", "volunteering",
"photography"). Cover different areas of life; do not guess anything about this particular user.
Return JSON: {"intent": "do" | "alternatives" | "explore", "reason": "<one short sentence>", "queries": ["...", ...]}"""


def judge_intent_queries(query: str, llm, context: str = "") -> tuple[str, str, list[str]]:
    """Intent plus search phrases for query-first recall, in the same single call."""
    user = f"Earlier in the conversation:\n{context}\n\nLatest message:\n{query}" if context else query
    try:
        out = llm.json("intent", QUERY_SYSTEM, user, temperature=0)
    except Exception as exc:
        return "do", f"intent check failed: {exc}", []
    intent = out.get("intent")
    intent = intent if intent in LEVELS else "do"
    queries = [q for q in out.get("queries", []) if isinstance(q, str) and q.strip()][:8]
    return intent, out.get("reason", ""), queries
