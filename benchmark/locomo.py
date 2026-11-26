"""Does the Widen plugin hurt Mem0 on LoCoMo (fact recall)?

On a "do" question the plugin returns Mem0's results unchanged, so with a temperature-0 answerer the answer is
identical. The only questions that can change are the ones the intent check wrongly sends down the exploration
path. So instead of comparing two noisy totals (Mem0 says its judge alone moves scores by about 1 point):

  intent   classify every LoCoMo question; misfire = anything other than "do"
  (later)  answer only the misfired questions with and without the plugin and compare

Usage: .venv/bin/python benchmark/locomo.py intent
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "src"))
sys.path.insert(0, str(ROOT))
from run import jsonl_append, jsonl_load, parallel  # noqa: E402
from widen.core.intent import judge_intent  # noqa: E402
from widen.llm import LLM  # noqa: E402

DATA = ROOT.parent / "data" / "locomo" / "locomo10.json"
OUT = ROOT / "results" / "locomo"
CATEGORIES = {1: "multi-hop", 2: "temporal", 3: "open-domain", 4: "single-hop", 5: "adversarial"}


def questions() -> list[dict]:
    rows = []
    for c in json.loads(DATA.read_text(encoding="utf-8")):
        for n, q in enumerate(c["qa"]):
            rows.append({"key": f"{c['sample_id']}|{n}", "question": q["question"], "category": q.get("category")})
    return rows


def stage_intent(llm) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "intent.jsonl"
    done = jsonl_load(path)
    todo = [q for q in questions() if q["key"] not in done]
    print(f"intent: {len(todo)} to run ({len(done)} cached)")

    def run(q):
        intent, reason = judge_intent(q["question"], llm)
        if reason.startswith("intent check failed"):
            print(f"  failed {q['key']}: {reason[:120]}", flush=True)
            return  # retry next run instead of counting an API error as "do"
        jsonl_append(path, {**q, "intent": intent, "reason": reason})

    parallel(run, todo)
    rows = list(jsonl_load(path).values())
    total = Counter(r["intent"] for r in rows)
    print(f"\n{len(rows)} questions: " + ", ".join(f"{k} {v}" for k, v in total.most_common()))
    miss = [r for r in rows if r["intent"] != "do"]
    print(f"misfire rate: {len(miss) / max(1, len(rows)):.2%}  (criterion: <= 2%)")
    by_cat = Counter(CATEGORIES.get(r["category"], r["category"]) for r in miss)
    print("misfires by category:", dict(by_cat))
    for r in miss[:20]:
        print(f"  [{r['intent']}] {r['question']}  -- {r['reason']}")


if __name__ == "__main__":
    llm = LLM()
    for stage in sys.argv[1:] or ["intent"]:
        {"intent": stage_intent}[stage](llm)
