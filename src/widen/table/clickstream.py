"""Build the 'people who read A went on to B' graph among the topic-table articles from Wikipedia clickstream.

This is our stand-in for a recommender's behaviour logs: Google trained on real "interest A,B -> C" transitions,
Pinterest's Pixie walks a user-item graph. Wikipedia publishes monthly counts of reader clicks from article A
to article B (pairs with <= 10 clicks are dropped): https://meta.wikimedia.org/wiki/Research:Wikipedia_clickstream

    python -m widen.table.clickstream data/clickstream/clickstream-enwiki-2026-10.tsv.gz [--level 4]

Writes data/clicks-l<level>.npz: a sparse matrix of click counts between table articles (row = from, col = to).
"""
from __future__ import annotations

import argparse
import gzip
from pathlib import Path

from .vital import DATA, load


def build(path: Path, level: int = 4) -> Path:
    import numpy as np
    rows, _ = load(level)
    index = {r["title"].replace(" ", "_"): i for i, r in enumerate(rows)}
    src, dst, cnt = [], [], []
    total = kept = 0
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            total += 1
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 4 or parts[2] != "link":
                continue
            a, b = index.get(parts[0]), index.get(parts[1])
            if a is None or b is None or a == b:
                continue
            src.append(a)
            dst.append(b)
            cnt.append(int(parts[3]))
            kept += 1
            if total % 5_000_000 == 0:
                print(f"  read {total:,} lines, kept {kept:,}", flush=True)
    out = DATA / f"clicks-l{level}.npz"
    np.savez_compressed(out, src=np.array(src, np.int32), dst=np.array(dst, np.int32), cnt=np.array(cnt, np.int64),
                        n=np.array(len(rows)))
    linked = len(set(src) | set(dst))
    print(f"read {total:,} lines; kept {kept:,} article->article clicks; {linked}/{len(rows)} articles have an edge")
    return out


def load_clicks(level: int = 4):
    """Row-normalised transition matrix P (scipy-free: dense float32, 6k x 6k is ~150 MB, so keep it sparse-ish)."""
    import numpy as np
    z = np.load(DATA / f"clicks-l{level}.npz")
    return z["src"], z["dst"], z["cnt"], int(z["n"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("--level", type=int, default=4)
    a = ap.parse_args()
    build(a.path, a.level)
