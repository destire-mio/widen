"""Unit tests for the Widen cascade with a tiny synthetic topic table and a fake model (no network, no data files)."""
import random

import numpy as np

from widen.adapters.mem0 import WidenMemory
from widen.core.clean import Tagged, clean
from widen.core.explore import bridge
from widen.core.neighbors import Neighbors
from widen.core.rank import Scored, coarse, excluded, fine, recall, rerank
from widen.llm import FakeLLM

ROWS = [
    {"title": "Noodle", "zh": "面条", "lead": "Food", "section": "Everyday life / Food / Dishes"},
    {"title": "Pasta", "zh": "意大利面", "lead": "Food", "section": "Everyday life / Food / Dishes"},
    {"title": "Fermentation", "zh": "发酵", "lead": "Process", "section": "Everyday life / Food / Preparation"},
    {"title": "Woodworking", "zh": "木工", "lead": "Craft", "section": "Technology / Crafts / Wood"},
    {"title": "Camping", "zh": "露营", "lead": "Outdoors", "section": "Everyday life / Recreation / Outdoors"},
    {"title": "Plankton", "zh": "浮游生物", "lead": "Organisms", "section": "Biology / Marine / Plankton"},
    {"title": "Weapon", "zh": "武器", "lead": "Tool", "section": "Technology / Military technology / Arms"},
]


def table():
    rng = np.random.default_rng(0)
    v = rng.normal(size=(len(ROWS), 16)).astype(np.float32)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    return Neighbors(ROWS, v)


def test_clean_drops_advice_and_merges_same_fact(tmp_path):
    mems = ["User makes hand-pulled noodles", "User has made noodles for ten years", "User was advised to rest"]
    llm = FakeLLM({"clean": {"tags": [
        {"memory": 1, "about": True, "kind": "skill", "topic": "makes noodles"},
        {"memory": 2, "about": True, "kind": "skill", "topic": "makes noodles"},
        {"memory": 3, "about": False, "kind": "background", "topic": "advice"},
    ]}})
    out = clean(mems, llm, tmp_path / "tags.json")
    assert [t.memory for t in out] == ["User makes hand-pulled noodles"]
    clean(mems, llm, tmp_path / "tags.json")  # second time: cached, no new call
    assert len(llm.calls) == 1


def test_excluded_covers_lit_siblings_and_blocked():
    nb = table()
    nb.c[1] = nb.c[0]                 # Pasta: a near-copy of Noodle in the same smallest section
    bad = excluded(nb, [0])          # Noodle is lit
    assert bad[0] and bad[1]          # itself and its close same-leaf sibling
    assert bad[6]                     # military technology is never offered
    assert not bad[2] and not bad[3]


def test_fine_rank_maps_shuffled_ids_and_marks_blocks():
    nb = table()
    cands = [Scored(2), Scored(3), Scored(4)]

    def answer(system, user):
        ranks = []
        for line in user.split("Candidates:\n")[1].splitlines():
            cid, rest = line.split(". ", 1)
            title = rest.split(" (")[0]
            ranks.append({"id": cid, "score": {"Fermentation": 8, "Woodworking": 7, "Camping": 6}[title],
                          "blocked": title == "Camping", "reason": "away overnight" if title == "Camping" else ""})
        return {"ranks": ranks}

    tagged = [Tagged("User can only rest on Monday afternoons", "constraint", "only monday afternoon free")]
    fine("周末做什么？", cands, tagged, nb, FakeLLM({"fine": answer}), random.Random(3))
    by = {c.article: c for c in cands}
    assert by[2].fine == 8 and by[3].fine == 7 and by[4].blocked == "away overnight"


def test_rerank_keeps_one_per_section_and_an_explore_slot():
    nb = table()
    a = Scored(2, fine=9, novelty=0.1)
    b = Scored(1, fine=8, novelty=0.1)       # Pasta
    c = Scored(0, fine=8, novelty=0.2)       # Noodle, same smallest section as Pasta -> only one of b/c
    d = Scored(3, fine=5, novelty=0.9)       # most novel that passed -> explore slot
    e = Scored(5, fine=2, novelty=1.0)       # failed the pass score
    f = Scored(4, fine=9, novelty=0.5, blocked="away overnight")
    picked = rerank([a, b, c, d, e, f], nb, n=3)
    assert f not in picked and e not in picked
    assert not (b in picked and c in picked)
    assert picked[-1] is d and d.slot == "explore"


def test_bridge_writes_one_direction_per_topic_and_sees_no_skills():
    nb = table()
    chosen = [Scored(2, fine=8, slot="ranked"), Scored(3, fine=6, slot="explore")]
    tagged = [Tagged("User makes noodles", "skill", "makes noodles"),
              Tagged("User cannot lift heavy things", "constraint", "cannot lift heavy things")]
    llm = FakeLLM({"bridge": {"directions": [{"id": "T1", "direction": "试做老面"}, {"id": "T2", "direction": "做个小木盒"}]}})
    out = bridge("周末做什么？", chosen, tagged, nb, llm)
    assert [d.text for d in out] == ["试做老面", "做个小木盒"] and out[1].slot == "explore"
    prompt = llm.calls[0][2]
    assert "cannot lift heavy things" in prompt and "makes noodles" not in prompt


class FakeMem0:
    def __init__(self):
        self.searched = []

    def search(self, query, *, filters=None, top_k=10, **kw):
        self.searched.append(top_k)
        return {"results": [{"memory": "User likes apples", "score": 0.9}]}

    def get_all(self, *, filters=None, top_k=20):
        return {"results": []}


def test_plain_question_returns_mem0_results_unchanged():
    mem0 = FakeMem0()
    llm = FakeLLM({"intent": {"intent": "do", "reason": "fact", "queries": []}})
    w = WidenMemory(mem0, llm, table=object())
    assert w.search("我上次说的项目叫什么？", filters={"user_id": "u"}) == mem0.search("x")
    assert mem0.searched[0] == 10 and [c[0] for c in llm.calls] == ["intent"]


def test_intent_error_falls_back_to_plain():
    def boom(system, user):
        raise RuntimeError("network down")
    mem0 = FakeMem0()
    w = WidenMemory(mem0, FakeLLM({"intent": boom}), table=object())
    assert w.search("周末做什么？")["results"][0]["memory"] == "User likes apples"


def test_coarse_prefers_novel_when_lambda_high():
    nb = table()
    feats = {"qrel": np.zeros(len(ROWS)), "walk": np.zeros(len(ROWS))}
    low = coarse([2, 3, 4, 5], [0], [0], nb, feats, lam=0.0, k=4)
    high = coarse([2, 3, 4, 5], [0], [0], nb, feats, lam=5.0, k=4)
    assert high[0].novelty >= low[0].novelty


def test_recall_comes_from_the_question_not_the_user():
    nb = table()
    qvec = nb.c[[3]]                                   # a "woodworking"-like search phrase
    pool, feats = recall(["woodworking"], [0], nb, None, per_query=2, qvec=qvec)
    assert pool[0] == 3 and 0 not in pool            # nearest to the phrase first; the lit article never
    assert feats["qrel"][3] > feats["qrel"][5]


def test_limits_are_distilled_once_per_memory_set(tmp_path):
    from widen.core.limits import distill_limits
    tagged = [Tagged("User has wrist tendinitis, can draw 4 hours a day", "constraint", "wrist tendinitis"),
              Tagged("User's C drive is full", "constraint", "full disk")]
    llm = FakeLLM({"limits": {"limits": [{"kind": "body", "limit": "腱鞘炎，每天最多画 4 小时"}]}})
    assert distill_limits(tagged, llm, tmp_path / "limits.json") == ["(body) 腱鞘炎，每天最多画 4 小时"]
    distill_limits(tagged, llm, tmp_path / "limits.json")
    assert len(llm.calls) == 1


def test_bridge_drops_directions_that_fail_the_final_check_and_falls_back():
    nb = table()
    chosen = [Scored(2, fine=9, slot="ranked"), Scored(3, fine=8, slot="ranked"),
              Scored(5, fine=7, slot="ranked"), Scored(4, fine=6, slot="explore")]
    llm = FakeLLM({"bridge": {"directions": [
        {"id": "T1", "direction": "每天给邻居打电话", "ok": False, "reason": "不喜欢打电话"},
        {"id": "T2", "direction": "做个小木盒", "ok": True},
        {"id": "T3", "direction": "去海边看浮游生物", "ok": True},
        {"id": "T4", "direction": "去露营一晚", "ok": True}]}})
    out = bridge("周末做什么？", chosen, [], nb, llm, limits=["(dislike) 不喜欢打电话"], n=3)
    assert [d.text for d in out] == ["做个小木盒", "去海边看浮游生物", "去露营一晚"]
    assert "不喜欢打电话" in llm.calls[0][2]


def test_rerank_with_spares_returns_backups():
    nb = table()
    cands = [Scored(i, fine=9 - i, novelty=i / 10) for i in (2, 3, 4, 5)]
    picked = rerank(cands, nb, n=2, spares=2)
    assert len(picked) >= 3 and any(p.slot == "explore" for p in picked)
