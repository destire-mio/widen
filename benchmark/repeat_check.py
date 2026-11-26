"""Do direction topics follow the QUESTION or only the person? One user, all 10 questions, 1 sample each.

    .venv/bin/python benchmark/repeat_check.py [user_id]
"""
import collections
import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "src"))
from widen.core.pipeline import Table, widen  # noqa: E402
from widen.llm import LLM  # noqa: E402

uid = sys.argv[1] if len(sys.argv) > 1 else "ma"
llm, table = LLM(), Table(4)
qs = json.loads((ROOT / "questions.json").read_text(encoding="utf-8"))
m = json.load(open(ROOT / "results-v2" / "memories" / f"{uid}.json"))
cache = ROOT / "results-v2" / "widen-cache"
seen = collections.Counter()
scores = []
for qi, q in enumerate(qs):
    out = widen(q, m["search"][q][:10], m["all"], llm, table, rng=random.Random(f"{uid}|{qi}|0"), cache_dir=cache)
    topics = [d.zh or d.title for d in out.directions]
    seen.update(set(topics))
    scores += [d.score or 0 for d in out.directions]
    print(f"\n{q}\n  phrases: {', '.join(out.queries)}")
    for d in out.directions:
        print(f"  [{d.slot} {d.score:.0f} | {d.zh or d.title}] {d.text}")
n = sum(seen.values())
print(f"\n{uid}: {n} directions, {len(seen)} distinct topics; topics in >=3 questions: "
      + ", ".join(f"{t}({k})" for t, k in seen.most_common() if k >= 3) + f"; mean fine score {statistics.mean(scores):.1f}")
