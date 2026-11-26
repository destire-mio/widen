"""Quick recall-quality check (TODO A10): 3 users x 2 questions, fine-rank scores of the candidate pool.

    .venv/bin/python benchmark/recall_check.py [label] [--lam 0.5] [--k 50]
Prints, per case, the best fine score, the mean of the 4 picks, how many candidates scored >= 7, and the picks.
"""
import argparse
import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "src"))
from widen.core.pipeline import Table, widen  # noqa: E402
from widen.llm import LLM  # noqa: E402

CASES = [("ma", "老马"), ("lin", "小林"), ("ye", "阿叶")]
QUESTIONS = ["周末想做个小项目，有什么点子？", "想搞个副业，有什么方向？"]

ap = argparse.ArgumentParser()
ap.add_argument("label", nargs="?", default="run")
ap.add_argument("--lam", type=float, default=0.5)
ap.add_argument("--k", type=int, default=50)
a = ap.parse_args()
llm, table = LLM(), Table(4)
R = table.rows
nm = lambda j: R[j]["zh"] or R[j]["title"]
cache = ROOT / "results" / "widen-cache"
summary = []
for uid, name in CASES:
    m = json.load(open(ROOT / "results" / "memories" / f"{uid}.json"))
    for q in QUESTIONS:
        out = widen(q, m["search"][q][:10], m["all"], llm, table, rng=random.Random(1), cache_dir=cache,
                    intent="explore", lam=a.lam, coarse_k=a.k)
        scores = sorted([c.fine for c in out.candidates if c.fine is not None and not c.blocked], reverse=True)
        picks = [d.score or 0 for d in out.directions]
        row = {"case": f"{name} / {q[:6]}", "best": scores[0] if scores else 0,
               "picks": round(statistics.mean(picks), 1) if picks else 0, "ge7": sum(s >= 7 for s in scores)}
        summary.append(row)
        print(f"\n{row['case']}: best {row['best']:.0f}, picks avg {row['picks']}, >=7: {row['ge7']}/{len(scores)}")
        for d in out.directions:
            print(f"  [{d.slot} {d.score:.0f} | {d.zh}] {d.text}")
print(f"\n[{a.label}] best avg {statistics.mean(r['best'] for r in summary):.1f}, "
      f"picks avg {statistics.mean(r['picks'] for r in summary):.1f}, "
      f">=7 avg {statistics.mean(r['ge7'] for r in summary):.1f}")
