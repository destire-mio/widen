"""Steps 4-7, the fourth path, built like search + recommendation:

  recall  -> from the QUESTION, not the user (search): its search phrases -> nearest table articles, plus readers'
             click paths out of those. Bench v2 recalled from the user only, so every question got the same
             topics (the noodle-shop owner got "chess" for 8 of 10 questions).
  coarse  -> a formula, no model: question relevance + best single-interest match - genericness + lam * novelty
  fine    -> one model call scores every candidate for this person and question AND marks hard-limit conflicts
             (fine rank + filter merged to save a call; candidates shuffled, no popularity shown, since LLM rankers
             are biased by position and popularity - Hou et al., LLMRank)
  rerank  -> one per smallest section; best scores first, one slot kept for the most novel candidate that still
             scored a pass (exploration shows up, but rarely)

Why not rank with the formula alone: with no click labels its features only measure "similar to what they
already have", which is exactly the circling we fight. It ranked pasta and ham first for the noodle-shop owner
and could not tell fermentation (good) from plankton (bad).
"""
from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np

from .clean import Tagged
from .light import Lit
from .neighbors import FAR_BLOCKED, Neighbors

INTEREST_KINDS = ("like", "skill", "resource")
PROFILE_KINDS = ("like", "skill", "resource", "background")
LIMIT_KINDS = ("constraint", "dislike")


@dataclass
class Scored:
    article: int
    coarse: float = 0.0
    novelty: float = 0.0
    fine: float | None = None     # 0-10 from the model
    blocked: str = ""             # reason, if a hard limit rules it out
    slot: str = ""                # "ranked" or "explore" after rerank


# ---------------- recall ----------------

def interests(lit: list[Lit], tagged: list[Tagged]) -> tuple[list[int], list[int]]:
    """(interest articles, all lit articles)."""
    kind = {t.memory: t.kind for t in tagged}
    lit_all = sorted({l.article for l in lit if l.article is not None})
    inter = sorted({l.article for l in lit if l.article is not None and kind.get(l.memory) in INTEREST_KINDS})
    return inter, lit_all


def seeds(inter: list[int], nb: Neighbors, rng: random.Random, k: int = 2) -> list[int]:
    """A random top-level section first, then a random interest inside it: a crowded area (food, for a
    noodle-shop owner) or a fact mentioned four times is no more likely to be the starting point."""
    by_top: dict[str, list[int]] = {}
    for a in inter:
        by_top.setdefault(nb.path[a][0], []).append(a)
    return [rng.choice(by_top[t]) for t in rng.sample(sorted(by_top), min(k, len(by_top)))]


def excluded(nb: Neighbors, lit_all: list[int], sibling_cos: float = 0.45) -> np.ndarray:
    """Lit articles, near-copies of them in the same smallest section (Xiangqi -> Go), sensitive areas.
    Only close siblings: excluding the whole section of a lit "Database" removed all of computer software,
    which was exactly where a backend engineer's best new topics were."""
    bad = np.array([r["section"].startswith(FAR_BLOCKED) for r in nb.rows])
    if lit_all:
        leaf_of = [tuple(p) for p in nb.path]
        sims = nb.c @ nb.c[lit_all].T                       # n x lit
        same_leaf = np.array([[leaf_of[j] == leaf_of[a] for a in lit_all] for j in range(len(nb.rows))])
        bad |= ((sims >= sibling_cos) & same_leaf).any(1)
        bad[lit_all] = True
    return bad


def embed_queries(queries: list[str], nb: Neighbors) -> np.ndarray:
    """Search phrases -> centered unit vectors in the same space as the table."""
    from ..table.vital import embed
    v = np.array(embed(queries, prefix="search_query: "), dtype=np.float32) - nb.mean
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def recall(queries: list[str], lit_all: list[int], nb: Neighbors, walker, *, per_query: int = 40,
           expand_from: int = 20, expand: int = 100, qvec: np.ndarray | None = None) -> tuple[list[int], dict]:
    """Query first, like search: candidates come from the QUESTION, not from the user's memories.
      1. each search phrase -> its nearest table articles (the question's answer space)
      2. readers' click paths out of the best of those (what people who read them go on to)
    The user only enters later, in ranking. Lit articles and their close siblings are excluded."""
    bad = excluded(nb, lit_all)
    feats: dict = {"qrel": np.zeros(len(nb.rows)), "walk": np.zeros(len(nb.rows))}
    if not queries:
        return [], feats
    q = qvec if qvec is not None else embed_queries(queries, nb)
    sims = nb.c @ q.T                                     # articles x queries
    feats["qrel"] = sims.max(1)
    pool: dict[int, None] = {}
    for k in range(sims.shape[1]):
        got = 0
        for j in np.argsort(-sims[:, k]):
            j = int(j)
            if not bad[j]:
                pool.setdefault(j, None)
                got += 1
                if got == per_query:
                    break
    if walker is not None:
        hits = [j for j in np.argsort(-feats["qrel"])[:expand_from * 3] if walker.has_paths(int(j))][:expand_from]
        if hits:
            x = walker._walk([int(j) for j in hits], walker.restart) / np.sqrt(walker.popularity)
            feats["walk"] = x
            got = 0
            for j in np.argsort(-x):
                j = int(j)
                if not bad[j] and j not in pool:
                    pool[j] = None
                    got += 1
                    if got == expand:
                        break
    return list(pool), feats


# ---------------- coarse rank ----------------

def coarse(pool: list[int], inter: list[int], lit_all: list[int], nb: Neighbors, feats: dict, *,
           lam: float = 0.5, k: int = 80) -> list[Scored]:
    """Question relevance first, then the person: + profile match (best single interest, DIN-style)
    - genericness + lam * distance from what they already have."""
    if not pool:
        return []
    idx = np.array(pool)
    c = nb.c
    z = lambda v: (v - v.mean()) / (v.std() + 1e-9)
    qrel = feats["qrel"][idx]
    walk = np.log(feats["walk"][idx] + 1e-12) if feats["walk"].any() else np.zeros(len(idx))
    match = (c[idx] @ c[inter].T).max(1) if inter else np.zeros(len(idx))
    novelty = 1 - (c[idx] @ c[lit_all].T).max(1) if lit_all else np.ones(len(idx))
    hub = nb._hubness()[idx]
    score = 1.0 * z(qrel) + 0.3 * z(walk) + 0.5 * z(match) - 0.5 * z(hub) + lam * z(novelty)
    order = np.argsort(-score)[:k]
    return [Scored(int(idx[i]), float(score[i]), float(novelty[i])) for i in order]


# ---------------- fine rank + hard-limit filter (one call) ----------------

FINE_SYSTEM = """You rank candidate topics for one user who asked an open question.
You get the question, a short profile of the user (likes, skills, resources, background - incomplete), the user's
known limits and dislikes, and numbered candidate topics. Every candidate is new to the user by design.
For each candidate:
- "score" 0-10: how likely this user would find a direction built on this topic interesting AND usable for THIS
  question. 0 = they would not care or it has nothing to do with the question; 10 = clearly appealing and doable.
  Do not reward a topic just for resembling what they already do.
- "blocked": true if a hard limit or dislike makes any direction from this topic infeasible for them
  (body, time, money, place, strong dislike), with a short "reason". Soft mismatches are not blocks.
Return JSON: {"ranks": [{"id": "<C1...>", "score": <0-10>, "blocked": true|false, "reason": "<short or empty>"}]}"""


def _labels(tagged: list[Tagged], kinds: tuple[str, ...], limit: int) -> list[str]:
    seen: list[str] = []
    for t in tagged:
        if t.kind in kinds and t.topic and f"({t.kind}) {t.topic}" not in seen:
            seen.append(f"({t.kind}) {t.topic}")
    return seen[:limit]


def fine(question: str, cands: list[Scored], tagged: list[Tagged], nb: Neighbors, llm, rng: random.Random,
         limits: list[str] | None = None) -> list[Scored]:
    if not cands:
        return []
    shuffled = cands[:]
    rng.shuffle(shuffled)
    ids = {f"C{n}": s for n, s in enumerate(shuffled, 1)}
    rows = nb.rows
    listing = "\n".join(f"{k}. {rows[s.article]['title']} ({rows[s.article]['zh']}): {rows[s.article]['lead']}"
                        for k, s in ids.items())
    profile = _labels(tagged, PROFILE_KINDS, 30) or ["(nothing known)"]
    lims = limits if limits is not None else [f"({t.kind}) {t.memory[:160]}" for t in tagged if t.kind in LIMIT_KINDS][:12]
    user = (f"Question: {question}\n\nProfile:\n" + "\n".join(f"- {x}" for x in profile) +
            "\n\nHard limits:\n" + "\n".join(f"- {x}" for x in (lims or ["(nothing known)"])) +
            f"\n\nCandidates:\n{listing}")
    for r in llm.json("fine", FINE_SYSTEM, user, temperature=0).get("ranks", []):
        s = ids.get(str(r.get("id", "")).strip().upper())
        if s is None:
            continue
        try:
            s.fine = max(0.0, min(10.0, float(r.get("score"))))
        except (TypeError, ValueError):
            continue
        if r.get("blocked") is True:
            s.blocked = str(r.get("reason") or "blocked")
    return cands


# ---------------- rerank ----------------

def rerank(cands: list[Scored], nb: Neighbors, n: int = 4, pass_score: float = 5.0, spares: int = 0) -> list[Scored]:
    """One per smallest section. n-1 slots by fine score, one slot for the most novel candidate that passed.
    With spares > 0, also returns that many extra ranked candidates and one extra explore candidate after the
    picks, in order, so a later check can drop a direction and fall back to the next one."""
    ok = [s for s in cands if s.fine is not None and not s.blocked and s.fine >= pass_score]
    ok.sort(key=lambda s: (-s.fine, -s.coarse))
    picked: list[Scored] = []
    leaves: set[tuple] = set()

    def add(s: Scored, slot: str) -> bool:
        leaf = tuple(nb.path[s.article])
        if leaf in leaves or s in picked:
            return False
        leaves.add(leaf)
        s.slot = slot
        picked.append(s)
        return True

    def best(pool, key, slot, k):
        got = 0
        for s in sorted(pool, key=key):
            if got >= k:
                break
            if add(s, slot):
                got += 1

    by_score = lambda s: (-s.fine, -s.coarse)
    by_novelty = lambda s: -s.novelty
    best(ok, by_score, "ranked", max(0, n - 1))                         # the picks ...
    best([s for s in ok if s not in picked], by_novelty, "explore", 1)  # ... one exploration slot
    best([s for s in ok if s not in picked], by_score, "ranked", n - len(picked))  # fill if nothing explored
    if spares:                                                          # backups for the final check
        best([s for s in ok if s not in picked], by_score, "ranked", spares)
        best([s for s in ok if s not in picked], by_novelty, "explore", 1)
    return picked
