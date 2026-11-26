"""Step 5, candidates from people's reading paths (the recommender's 'people who saw A went on to B').

Two stages, like a recommender's candidate generation + re-rank:
  1. Random walk with restart (personalised PageRank, as in Pinterest's Pixie) from the seed articles over the
     Wikipedia clickstream graph; divide by global popularity so hub articles don't win everywhere; keep the
     top `pool` articles. This is the relevance gate: only places readers actually go.
  2. Re-rank the pool by  -log(1 + relevance rank) + lam * novelty,  novelty = vector distance from the seed.
     lam is the explore/exploit knob: 0 = the common next step, ~1 = reachable but different. lam ~2 drifted
     to dinosaurs and pangolins from "bread" and "spice", so the benchmark sweeps 0..1.
Seeds whose article has few outgoing clicks fall back to the section tree + vectors (Neighbors).
"""
from __future__ import annotations

import numpy as np

from ..table.clickstream import load_clicks
from .neighbors import FAR_BLOCKED, Neighbors


class ClickWalk:
    def __init__(self, nb: Neighbors, level: int = 4, restart: float = 0.3, iters: int = 40,
                 min_clicks: int = 100, pool: int = 200, min_cos: float = 0.05):
        self.nb = nb
        src, dst, cnt, n = load_clicks(level)
        # Drop clicks between articles whose meanings don't touch (~8% of edges): etymology links
        # ("Angling -> Old English"), diseases named in novels ("Little Women -> Scarlet fever").
        keep = np.einsum("ij,ij->i", nb.c[src], nb.c[dst]) >= min_cos
        src, dst, cnt = src[keep], dst[keep], cnt[keep]
        self.src, self.dst, self.n = src, dst, n
        self.out = np.bincount(src, weights=cnt, minlength=n).astype(np.float64)
        self.w = cnt / self.out[src]
        self.restart, self.iters, self.min_clicks, self.pool = restart, iters, min_clicks, pool
        self.blocked = np.array([r["section"].startswith(FAR_BLOCKED) for r in nb.rows])
        self.popularity = self._walk(np.arange(n), 0.15)

    def _walk(self, seeds, restart: float) -> np.ndarray:
        e = np.zeros(self.n)
        e[seeds] = 1 / len(seeds)
        x = e.copy()
        dangling = self.out == 0
        for _ in range(self.iters):
            y = np.bincount(self.dst, weights=x[self.src] * self.w, minlength=self.n)
            x = restart * e + (1 - restart) * (y + x[dangling].sum() * e)
        return x

    def has_paths(self, i: int) -> bool:
        return self.out[i] >= self.min_clicks

    def rank(self, seed: int, lam: float, exclude: set[int], k: int) -> list[int]:
        if not self.has_paths(seed):  # too few readers leave this page: fall back to tree + vectors
            return self.nb.adjacent(seed, k, exclude=exclude) if lam == 0 else self.nb.far(seed, k, exclude=exclude)
        x = self._walk([seed], self.restart)
        rel = x / np.sqrt(self.popularity)
        leaf = self.nb.path[seed]
        ok = (x > 0) & ~self.blocked
        ok[seed] = False
        for j in exclude:
            ok[j] = False
        ok &= np.array([p != leaf for p in self.nb.path])  # same smallest section = same kind (Xiangqi -> Go)
        pool = [int(j) for j in np.argsort(-np.where(ok, rel, -1.0))[: self.pool] if ok[j]]
        if not pool:
            return []
        novelty = np.array([1 - float(self.nb.c[j] @ self.nb.c[seed]) for j in pool])
        nz = (novelty - novelty.mean()) / (novelty.std() + 1e-9)
        score = -np.log1p(np.arange(len(pool))) + lam * nz
        return [pool[k] for k in np.argsort(-score)[:k]]
