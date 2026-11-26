"""Benchmark: does an assistant with Mem0 memory only circle around what it remembers?

Stages (each cached, so a rerun resumes where it stopped):
  generate  turn each persona sheet (personas/) into ~60 dated chat sessions (users/)
  audit     check which facts each session really revealed (planned != actual)
  repair    regenerate sessions that leaked unplanned facts, re-audit them
  ingest  feed each mock user's chat history into Mem0, save what Mem0 extracted
  link    map each Mem0 memory back to the persona fact it expresses
  answer  every user x question x arm x sample -> 5 ideas
  judge   for each idea: which memory (if any) it builds on
  fit     is each idea suitable for this person (judged against the persona sheet)
  group   per user x question x arm: how many distinct ideas
  report  tables + the pre-registered verdict (see SPEC.md section 1)

Usage: .venv/bin/python benchmark/run.py [stage ...]   (no stage = all)
"""
from __future__ import annotations

import json
import os
import random
import statistics
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "src"))
from widen.llm import LLM  # noqa: E402

RESULTS = ROOT / os.environ.get("WIDEN_BENCH_RUN", "results")  # v1 = results, v2 = results-v2
# WIDEN_BENCH_SET=holdout switches to personas-holdout/, users-holdout/, questions-holdout.json: users and
# questions never looked at while the plugin was developed.
_SET = os.environ.get("WIDEN_BENCH_SET", "")
PERSONAS = ROOT / ("personas" + (f"-{_SET}" if _SET else ""))
USERS = ROOT / ("users" + (f"-{_SET}" if _SET else ""))
QUESTIONS = ROOT / ("questions" + (f"-{_SET}" if _SET else "") + ".json")
SAMPLES = 3
IDEAS = 5
WORKERS = 8

ARMS_ALL = {
    "A_none": {"memory": False, "nudge": False, "temperature": 0.7},
    "B_memory": {"memory": True, "nudge": False, "temperature": 0.7},
    "C_memory_nudge": {"memory": True, "nudge": True, "temperature": 0.7},
    "D_memory_hot": {"memory": True, "nudge": False, "temperature": 1.3},
    # Widen plugin: cleaned memories + exploration directions, no instruction (E1) / one light hint (E2).
    "E1_widen": {"memory": True, "nudge": False, "temperature": 0.7, "widen": True, "hint": False},
    "E2_widen_hint": {"memory": True, "nudge": False, "temperature": 0.7, "widen": True, "hint": True},
    # Directions only: the answering model gets no memories (fit was already checked by the plugin).
    "E3_widen_dirs": {"memory": True, "nudge": False, "temperature": 0.7, "widen": True, "hint": False,
                      "mem_out": False},
    "E4_widen_dirs_lam1": {"memory": True, "nudge": False, "temperature": 0.7, "widen": True, "hint": False,
                           "mem_out": False, "lam": 1.0},
}

ANSWER_SYSTEM = "你是一个乐于助人的助手。"
MEMORY_BLOCK = "\n\n以下是你记得的关于这位用户的信息：\n{memories}"
NUDGE = "\n\n注意：不要局限于用户过去的经历和兴趣，尽量给出多样、新颖、用户可能没想到的想法。"
ANSWER_FORMAT = f"请给出 {IDEAS} 个具体的点子，每个一句话。只返回 JSON：{{\"ideas\": [\"...\", ...]}}"

KIND_SYSTEM = """下面是 AI 助手记住的关于某位用户的若干条记忆。给每条记忆标一个种类：
like = 只是喜欢、爱好（不代表擅长）；skill = 会的技能、职业经验；resource = 手上的资源、人脉、数据、渠道；
dislike = 讨厌或回避的东西；constraint = 时间、金钱、身体等限制条件；other = 以上都不是。
只返回 JSON：{"kinds": [{"id": <编号>, "kind": "<种类>"}]}"""

JUDGE_SYSTEM = """你是评审。给你一位用户的记忆列表（带编号）和一组点子（带编号）。
对每个点子判断：它的主题或方向，是不是从某一条记忆延伸出来的？
“延伸出来”指：点子围绕那条记忆里的爱好、职业、技能、资源或人展开；如果不知道这条记忆，一般不会想到这个点子。
只是顺带提一句、或者泛泛适合所有人的点子，不算延伸。
如果是，给出最主要的那一条记忆编号；如果不是，记忆编号填 0。
只返回 JSON：{"labels": [{"idea": <点子编号>, "memory": <记忆编号或 0>}]}"""

GROUP_SYSTEM = """给你一组编号的点子。把意思基本相同的点子归为一组（换个说法、换个细节但本质一样的算同一组）。
每个编号必须且只能出现在一个组里。只返回 JSON：{"groups": [[<编号>, ...], ...]}"""

_lock = threading.Lock()


# ---------- small cache helpers ----------

# WIDEN_BENCH_ARMS=A_none,B_memory,... runs a subset of arms (the held-out test runs only the pre-registered ones).
ARMS = {k: v for k, v in ARMS_ALL.items()
        if not os.environ.get("WIDEN_BENCH_ARMS") or k in os.environ["WIDEN_BENCH_ARMS"].split(",")}


def jsonl_load(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {r["key"]: r for r in rows}


def jsonl_append(path: Path, row: dict) -> None:
    with _lock, path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def parallel(fn, items) -> None:
    items = list(items)
    if not items:
        return
    done = 0
    with ThreadPoolExecutor(WORKERS) as pool:
        for _ in pool.map(fn, items):
            done += 1
            if done % 20 == 0 or done == len(items):
                print(f"  {done}/{len(items)}", flush=True)


def load_users() -> list[dict]:
    """Persona sheets; generated sessions are attached under "sessions" when they exist."""
    users = []
    for p in sorted((PERSONAS).glob("*.json")):
        u = json.loads(p.read_text(encoding="utf-8"))
        chats = USERS / p.name
        u["sessions"] = json.loads(chats.read_text(encoding="utf-8")) if chats.is_file() else []
        users.append(u)
    return users


def load_questions() -> list[str]:
    return json.loads((QUESTIONS).read_text(encoding="utf-8"))


# ---------- generate chats from persona sheets ----------

SESSIONS = 60
START_DATE = "2026-03-02"

GEN_SYSTEM = """你在为一个测试编写一段逼真的“用户和 AI 助手”的聊天记录。
用户是普通人，口语化，不会刻意介绍自己。助手回答简短实用（每次 2 到 4 句）。
写 2 到 4 轮来回（user 和 assistant 交替，user 先说）。
只写下面要求的内容，不要额外编造用户的爱好、职业、家人、资源或限制。
只返回 JSON：{"turns": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}"""


def schedule(persona: dict, rng: random.Random) -> list[dict]:
    """Spread every fact's mentions over the timeline, at most two facts per session, rest is noise."""
    mentions = []
    for f in persona["facts"]:
        n = f["times"]
        for k in range(n):
            mentions.append(((k + rng.uniform(0.2, 0.8)) / n, k, f))
    mentions.sort(key=lambda m: m[0])
    slots: list[list] = []
    for m in mentions:
        if slots and len(slots[-1]) < 2 and all(x[2]["id"] != m[2]["id"] for x in slots[-1]) and rng.random() < 0.9:
            slots[-1].append(m)
        else:
            slots.append([m])
    noise = list(persona["noise_topics"])
    rng.shuffle(noise)
    n_noise = max(0, SESSIONS - len(slots))
    noise = (noise * (n_noise // max(1, len(noise)) + 1))[:n_noise]
    plan = [{"facts": [(k, f) for _, k, f in slot]} for slot in slots]
    for topic in noise:  # insert noise at random places, keeping the fact order
        plan.insert(rng.randrange(len(plan) + 1), {"noise": topic})
    return plan


def fact_brief(k: int, f: dict) -> str:
    how = "明说出来" if f["say"] == "explicit" else "不要直接说出来，只通过细节让人能推断出来"
    if "before" in f:  # outdated / contradicted: earlier sessions only get the old state
        if f["times"] == 1:
            text = f"{f['before']}；但{f['after']}"
        else:
            text = f["after"] if k == f["times"] - 1 else f["before"]
    else:
        text = f["text"].split("（陷阱")[0]
    return f"- {text}：{how}"


def gen_session(u: dict, slot: dict, llm) -> list[dict]:
    if "noise" in slot:
        task = f"用户是一个普通人。\n这段聊天的话题：{slot['noise']}。这段里不要透露用户的任何个人信息。"
    else:
        briefs = "\n".join(fact_brief(k, f) for k, f in slot["facts"])
        task = ("用户是一个普通人。\n自己选一个日常、自然的话题（用户来问助手一个实际问题），"
                f"在聊天中顺带透露下面的信息，除此之外不透露任何个人信息：\n{briefs}")
    turns = llm.json("generate", GEN_SYSTEM, task, temperature=1.0).get("turns", [])
    return [t for t in turns if t.get("role") in ("user", "assistant") and t.get("content")]


def stage_generate(users, questions, llm) -> None:
    import datetime as dt
    out_dir = USERS
    out_dir.mkdir(exist_ok=True)
    for u in users:
        path = out_dir / f"{u['id']}.json"
        if path.is_file():
            continue
        plan = schedule(u, random.Random(u["id"]))
        start = dt.date.fromisoformat(START_DATE)
        print(f"generate: {u['name']} ({len(plan)} sessions)", flush=True)

        def run(item):
            i, slot = item
            slot["turns"] = gen_session(u, slot, llm)
            slot["date"] = (start + dt.timedelta(days=4 * i)).isoformat()

        parallel(run, list(enumerate(plan)))
        sessions = [{"date": x["date"], "noise": x.get("noise"), "facts": [f["id"] for _, f in x.get("facts", [])],
                     "turns": x["turns"]} for x in plan if x.get("turns")]
        path.write_text(json.dumps(sessions, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {len(sessions)} sessions", flush=True)


AUDIT_SYSTEM = """给你一段用户和 AI 助手的聊天，以及一份关于这位用户的信息清单（带编号）。
找出这段聊天里，用户明说或者能让人合理推断出的信息。只算用户这一方透露的。
只返回 JSON：{"revealed": ["<编号>", ...]}"""


def fact_listing(u: dict) -> str:
    return "\n".join(f"{f['id']}. " + (f"{f['before']} / {f['after']}" if "before" in f else f["text"].split("（陷阱")[0])
                     for f in u["facts"])


def audit_session(u: dict, session: dict, llm) -> list[str]:
    chat = "\n".join(("用户：" if t["role"] == "user" else "助手：") + t["content"] for t in session["turns"])
    out = llm.json("audit", AUDIT_SYSTEM, f"信息清单：\n{fact_listing(u)}\n\n聊天：\n{chat}", temperature=0)
    return [x for x in out.get("revealed", []) if isinstance(x, str)]


def write_audit(u: dict, found: list) -> list[dict]:
    rows = []
    for f in u["facts"]:
        planned = sum(f["id"] in x["facts"] for x in u["sessions"])
        actual = sum(f["id"] in (found[i] or []) for i in range(len(found)))
        leaked = sum(f["id"] in (found[i] or []) and f["id"] not in u["sessions"][i]["facts"] for i in range(len(found)))
        rows.append({"id": f["id"], "kind": f["kind"], "times": f["times"], "planned": planned,
                     "actual": actual, "leaked": leaked})
    (USERS / f"{u['id']}.audit.json").write_text(
        json.dumps({"per_session": found, "per_fact": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    return rows


def print_audit(u: dict, rows: list[dict]) -> None:
    bad = [r for r in rows if r["actual"] != r["planned"] or r["leaked"]]
    print(f"  {u['name']}: {len(rows) - len(bad)}/{len(rows)} facts exact", flush=True)
    for r in bad:
        print(f"    {r['id']:<4} {r['kind']:<11} planned {r['planned']} actual {r['actual']} leaked {r['leaked']}")


def stage_audit(users, questions, llm) -> None:
    """Which facts did each generated session actually reveal? Planned counts are not real counts."""
    for u in users:
        if (USERS / f"{u['id']}.audit.json").is_file() or not u["sessions"]:
            continue
        found = [None] * len(u["sessions"])

        def run(i):
            found[i] = audit_session(u, u["sessions"][i], llm)

        print(f"audit: {u['name']}", flush=True)
        parallel(run, range(len(u["sessions"])))
        print_audit(u, write_audit(u, found))


# Noise topics that say nothing about who is asking (persona-specific noise leaked facts).
NEUTRAL_NOISE = [
    "量子计算机到底快在哪", "解释一下什么是通货膨胀", "一个英文单词 serendipity 的用法", "怎么挑西瓜",
    "怎么去除衣服上的油渍", "家里 Wi-Fi 信号差怎么办", "空调开多少度最省电", "快递显示签收但没收到怎么办",
    "黑洞是怎么形成的", "为什么天空是蓝色的", "解释一下新闻里说的降准", "地球上最深的海沟在哪",
    "怎么判断鸡蛋新不新鲜", "为什么飞机能飞起来", "恐龙是怎么灭绝的", "解释一下什么是区块链",
    "冬天为什么容易静电", "怎么记住一串长数字", "猫为什么喜欢纸箱", "金字塔是怎么建起来的",
]


def stage_repair(users, questions, llm, tries: int = 3) -> None:
    """Regenerate sessions that revealed facts they were not planned to reveal, then re-audit them."""
    for u in users:
        audit_path = USERS / f"{u['id']}.audit.json"
        if not audit_path.is_file():
            continue
        found = json.loads(audit_path.read_text(encoding="utf-8"))["per_session"]
        rng = random.Random(u["id"] + "-repair")
        changed = False
        for attempt in range(tries):
            bad = [i for i, x in enumerate(u["sessions"]) if set(found[i] or []) - set(x["facts"])]
            if not bad:
                break
            print(f"repair: {u['name']} try {attempt + 1}, {len(bad)} sessions leak", flush=True)

            def run(i):
                x = u["sessions"][i]
                if x["noise"]:
                    x["noise"] = rng.choice(NEUTRAL_NOISE)
                    slot = {"noise": x["noise"]}
                else:
                    by_id = {f["id"]: f for f in u["facts"]}
                    earlier = [y for y in u["sessions"][:i]]
                    slot = {"facts": [(sum(fid in y["facts"] for y in earlier), by_id[fid]) for fid in x["facts"]]}
                x["turns"] = gen_session(u, slot, llm)
                found[i] = audit_session(u, x, llm)

            parallel(run, bad)
            changed = True
        if changed:
            (USERS / f"{u['id']}.json").write_text(
                json.dumps(u["sessions"], ensure_ascii=False, indent=1), encoding="utf-8")
            print_audit(u, write_audit(u, found))


# ---------- Mem0 ----------

def mem0_client(llm, store: Path):
    """Mem0 with the same DeepSeek key as everything else, local Ollama embeddings, on-disk Qdrant."""
    os.environ.setdefault("MEM0_TELEMETRY", "False")
    from mem0 import Memory

    store.mkdir(parents=True, exist_ok=True)
    config = {
        "llm": {"provider": "deepseek", "config": {
            "model": llm.model, "api_key": llm.client.api_key, "temperature": 0.1,
            "deepseek_base_url": str(llm.client.base_url).rstrip("/")}},
        "embedder": {"provider": "ollama", "config": {
            "model": "nomic-embed-text", "embedding_dims": 768, "ollama_base_url": "http://localhost:11434"}},
        "vector_store": {"provider": "qdrant", "config": {
            "collection_name": "widen_bench", "embedding_model_dims": 768, "path": str(store / "qdrant"),
            "on_disk": True}},
        "history_db_path": str(store / "history.db"),
    }
    return Memory.from_config(config)


def _memories(result) -> list[str]:
    items = result.get("results", result) if isinstance(result, dict) else result
    return [i["memory"] for i in items if i.get("memory")]


def ingest_user(u: dict, llm, out: Path) -> None:
    """One Mem0 store per user, so users can be ingested in parallel; sessions go in date order."""
    m = mem0_client(llm, RESULTS / "mem0" / u["id"])
    print(f"ingest: {u['name']} ({len(u['sessions'])} sessions)", flush=True)
    for n, session in enumerate(u["sessions"], 1):
        m.add(session["turns"], user_id=u["id"], metadata={"date": session["date"]})
        if n % 10 == 0:
            print(f"  {u['name']} {n}/{len(u['sessions'])}", flush=True)
    who = {"user_id": u["id"]}
    memories = _memories(m.get_all(filters=who, top_k=1000))
    retrieved = {q: _memories(m.search(q, filters=who, top_k=10)) for q in load_questions()}
    (out / f"{u['id']}.json").write_text(json.dumps(
        {"all": memories, "search": retrieved}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  {u['name']}: Mem0 kept {len(memories)} memories", flush=True)


def stage_ingest(users, questions, llm) -> None:
    out = RESULTS / "memories"
    out.mkdir(parents=True, exist_ok=True)
    todo = [u for u in users if u["sessions"] and not (out / f"{u['id']}.json").is_file()]
    if not todo:
        print("ingest: cached")
        return
    with ThreadPoolExecutor(len(todo)) as pool:
        list(pool.map(lambda u: ingest_user(u, llm, out), todo))


def user_memories(uid: str) -> dict:
    return json.loads((RESULTS / "memories" / f"{uid}.json").read_text(encoding="utf-8"))


# ---------- stages ----------

LINK_SYSTEM = """给你两份清单：A 是 AI 记忆系统存下的关于某位用户的记忆（带编号），B 是这位用户的真实信息（带编号）。
对 A 里的每一条记忆，找出它说的是 B 里的哪一条信息。如果它不对应 B 里的任何一条（比如只是助手给过的建议、或闲聊内容），填 "none"。
只返回 JSON：{"links": [{"memory": <A 的编号>, "fact": "<B 的编号或 none>"}]}"""


def stage_link(users, questions, llm) -> None:
    """Map every Mem0 memory back to the persona fact it expresses (ground truth for kind, trap, exposure)."""
    path = RESULTS / "links.json"
    links = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    for u in users:
        if u["id"] in links or not (RESULTS / "memories" / f"{u['id']}.json").is_file():
            continue
        mems = user_memories(u["id"])["all"]
        ids = {f["id"] for f in u["facts"]}
        result = [None] * len(mems)
        for lo in range(0, len(mems), 40):  # chunks keep the JSON answer short and reliable
            chunk = mems[lo:lo + 40]
            listing = "\n".join(f"{lo + n}. {m}" for n, m in enumerate(chunk, 1))
            out = llm.json("link", LINK_SYSTEM, f"A：\n{listing}\n\nB：\n{fact_listing(u)}", temperature=0)
            for row in out.get("links", []):
                if isinstance(row, dict) and isinstance(row.get("memory"), int) and 1 <= row["memory"] <= len(mems):
                    result[row["memory"] - 1] = row.get("fact") if row.get("fact") in ids else None
        links[u["id"]] = result
        print(f"link: {u['name']} {sum(x is not None for x in result)}/{len(mems)} memories map to a persona fact")
    path.write_text(json.dumps(links, ensure_ascii=False, indent=1), encoding="utf-8")


def answer_key(uid, qi, arm, s):
    return f"{uid}|{qi}|{arm}|{s}"


WIDEN_HINT = "\n\n（以上记忆可能不完整。）"
DIRECTIONS_BLOCK = "\n\n可能相关的方向：\n{directions}"
_table = None
_table_lock = threading.Lock()


def widen_context(u: dict, qi: int, s: int, questions: list[str], llm, cfg: dict | None = None) -> dict | None:
    """What the Widen plugin hands the answering model: cleaned memories + directions (same as WidenMemory.search)."""
    global _table
    from widen.core.pipeline import Table, widen
    with _table_lock:
        if _table is None:
            _table = Table(4)
    q = questions[qi]
    mem = user_memories(u["id"])
    try:
        cfg = cfg or {}
        out = widen(q, mem["search"][q], mem["all"], llm, _table, rng=random.Random(f"{u['id']}|{qi}|{s}"),
                    cache_dir=RESULTS / "widen-cache", lam=cfg.get("lam", 0.5))
    except Exception as exc:
        print(f"  widen failed {u['id']} {qi} {s}: {exc}", flush=True)
        return None
    system = ""
    if out.intent != "do":
        if cfg.get("mem_out", True):
            system += MEMORY_BLOCK.format(memories="\n".join(f"- {t.memory}" for t in out.memories) or "（无）")
        if out.directions:
            system += DIRECTIONS_BLOCK.format(directions="\n".join(f"- {d.text}" for d in out.directions))
    else:  # plain task: the plugin returns Mem0's results unchanged
        system += MEMORY_BLOCK.format(memories="\n".join(f"- {m}" for m in mem["search"][q][:10]) or "（无）")
    log = {"intent": out.intent, "memories": [t.memory for t in out.memories],
           "directions": [{"text": d.text, "slot": d.slot, "topic": d.zh or d.title, "score": d.score} for d in out.directions],
           "blocked": [{"topic": _table.rows[c.article]["zh"] or _table.rows[c.article]["title"], "reason": c.blocked}
                       for c in out.candidates if c.blocked]}
    return {"system": system, "log": log}


def stage_answer(users, questions, llm) -> None:
    path = RESULTS / "answers.jsonl"
    done = jsonl_load(path)
    jobs = [(u, qi, arm, s) for u in users for qi in range(len(questions)) for arm in ARMS for s in range(SAMPLES)
            if answer_key(u["id"], qi, arm, s) not in done]
    print(f"answer: {len(jobs)} to run ({len(done)} cached)")

    def run(job):
        u, qi, arm, s = job
        cfg, q = ARMS[arm], questions[qi]
        system = ANSWER_SYSTEM
        extra = {}
        if cfg.get("widen"):
            out = widen_context(u, qi, s, questions, llm, cfg)
            if out is None:
                return
            system += out["system"]
            extra = {"widen": out["log"]}
        elif cfg["memory"]:
            mems = user_memories(u["id"])["search"][q][:10]
            system += MEMORY_BLOCK.format(memories="\n".join(f"- {m}" for m in mems) or "（无）")
        if cfg.get("hint"):
            system += WIDEN_HINT
        if cfg["nudge"]:
            system += NUDGE
        try:
            ideas = llm.json("answer", system, f"{q}\n\n{ANSWER_FORMAT}", temperature=cfg["temperature"]).get("ideas", [])
        except Exception as exc:  # keep going; a missing row is retried next run
            print(f"  failed {job[1:]}: {exc}", flush=True)
            return
        ideas = [i for i in ideas if isinstance(i, str) and i.strip()][:IDEAS]
        jsonl_append(path, {"key": answer_key(u["id"], qi, arm, s), "user": u["id"], "q": qi, "arm": arm,
                            "sample": s, "ideas": ideas, **extra})

    parallel(run, jobs)


def stage_judge(users, questions, llm) -> None:
    answers = jsonl_load(RESULTS / "answers.jsonl")
    path = RESULTS / "judged.jsonl"
    done = jsonl_load(path)
    jobs = [a for k, a in answers.items() if k not in done]
    print(f"judge: {len(jobs)} to run ({len(done)} cached)")
    mem_cache = {u["id"]: user_memories(u["id"])["all"] for u in users}

    def run(a):
        mems = mem_cache[a["user"]]
        user = ("记忆：\n" + "\n".join(f"{n}. {m}" for n, m in enumerate(mems, 1)) +
                "\n\n点子：\n" + "\n".join(f"{n}. {i}" for n, i in enumerate(a["ideas"], 1)))
        try:
            labels = llm.json("judge", JUDGE_SYSTEM, user, temperature=0).get("labels", [])
        except Exception as exc:
            print(f"  failed {a['key']}: {exc}", flush=True)
            return
        by_idea = {l.get("idea"): l.get("memory") for l in labels if isinstance(l, dict)}
        cited = []
        for n in range(1, len(a["ideas"]) + 1):
            m = by_idea.get(n)
            cited.append(m if isinstance(m, int) and 1 <= m <= len(mems) else 0)
        jsonl_append(path, {"key": a["key"], "memory": cited})

    parallel(run, jobs)


FIT_SYSTEM = """你是评审。给你一位用户的真实情况，和一组给他的点子（带编号）。
判断每个点子对这个人是不是“合适”：他做得了（技能、时间、钱、身体都允许），也不违背他讨厌的东西，做起来有实际意义。
不要求点子和他的过去有关，和他过去无关的新方向也可以合适。只看现在的情况，过时的信息以后来的说法为准。
只返回 JSON：{"fit": [{"idea": <编号>, "ok": true 或 false}]}"""


def persona_truth(u: dict) -> str:
    lines = []
    for f in u["facts"]:
        text = f["after"] if "before" in f else f["text"].split("（陷阱")[0]
        if f["id"] == "R1":
            text += "（但他对这一行完全不懂）"
        lines.append(f"- {text}")
    return f"{u['summary']}\n" + "\n".join(lines)


def stage_fit(users, questions, llm) -> None:
    """Is each idea feasible and suitable for this person? Judged against the persona sheet, not Mem0."""
    answers = jsonl_load(RESULTS / "answers.jsonl")
    path = RESULTS / "fit.jsonl"
    done = jsonl_load(path)
    truth = {u["id"]: persona_truth(u) for u in users}
    jobs = [a for k, a in answers.items() if k not in done]
    print(f"fit: {len(jobs)} to run ({len(done)} cached)")

    def run(a):
        user = (f"用户的真实情况：\n{truth[a['user']]}\n\n问题：{questions[a['q']]}\n\n点子：\n" +
                "\n".join(f"{n}. {i}" for n, i in enumerate(a["ideas"], 1)))
        try:
            out = llm.json("fit", FIT_SYSTEM, user, temperature=0).get("fit", [])
        except Exception as exc:
            print(f"  failed {a['key']}: {exc}", flush=True)
            return
        ok = {r.get("idea"): bool(r.get("ok")) for r in out if isinstance(r, dict)}
        jsonl_append(path, {"key": a["key"], "ok": [ok.get(n, False) for n in range(1, len(a["ideas"]) + 1)]})

    parallel(run, jobs)


def stage_group(users, questions, llm) -> None:
    answers = jsonl_load(RESULTS / "answers.jsonl")
    path = RESULTS / "groups.jsonl"
    done = jsonl_load(path)
    pools = defaultdict(list)
    for a in answers.values():
        pools[f"{a['user']}|{a['q']}|{a['arm']}"] += a["ideas"]
    jobs = [(k, ideas) for k, ideas in pools.items() if k not in done]
    print(f"group: {len(jobs)} to run ({len(done)} cached)")

    def run(job):
        key, ideas = job
        listing = "\n".join(f"{n}. {i}" for n, i in enumerate(ideas, 1))
        try:
            groups = llm.json("group", GROUP_SYSTEM, listing, temperature=0).get("groups", [])
        except Exception as exc:
            print(f"  failed {key}: {exc}", flush=True)
            return
        seen, count = set(), 0
        for g in groups:
            members = {i for i in g if isinstance(i, int) and 1 <= i <= len(ideas)} - seen
            if members:
                count += 1
                seen |= members
        jsonl_append(path, {"key": key, "ideas": len(ideas), "distinct": count + len(ideas) - len(seen)})

    parallel(run, jobs)


def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


KIND_ORDER = ("like", "skill", "resource", "dislike", "constraint", "background")
KIND_NAMES = {"like": "只是喜好", "skill": "会的技能", "resource": "手上的资源", "dislike": "讨厌的",
              "constraint": "限制条件", "background": "背景"}


def stage_report(users, questions, llm) -> None:
    answers = jsonl_load(RESULTS / "answers.jsonl")
    judged = jsonl_load(RESULTS / "judged.jsonl")
    groups = jsonl_load(RESULTS / "groups.jsonl")
    fits = jsonl_load(RESULTS / "fit.jsonl")
    links = json.loads((RESULTS / "links.json").read_text(encoding="utf-8"))
    by_user = {u["id"]: u for u in users}
    facts = {u["id"]: {f["id"]: f for f in u["facts"]} for u in users}
    exposure = {}  # (user, fact) -> sessions that really revealed it (from the audit)
    for u in users:
        for row in json.loads((USERS / f"{u['id']}.audit.json").read_text(encoding="utf-8"))["per_fact"]:
            exposure[(u["id"], row["id"])] = row["actual"]

    # every judged idea -> the persona fact behind the memory it builds on (or None)
    rows = []  # (user, q, arm, idea, memory text or "", fact id or None)
    for key, a in answers.items():
        j = judged.get(key)
        if not j:
            continue
        mems = user_memories(a["user"])["all"]
        oks = fits.get(key, {}).get("ok", [None] * len(a["ideas"]))
        for idea, m, ok in zip(a["ideas"], j["memory"], oks):
            fact = links[a["user"]][m - 1] if m else None
            rows.append((a["user"], a["q"], a["arm"], idea, mems[m - 1] if m else "", fact, bool(m), ok))

    def share(arm, test, user=None):
        sel = [r for r in rows if r[2] == arm and (user is None or r[0] == user)]
        return sum(test(r) for r in sel) / len(sel) if sel else 0.0

    cited = lambda r: r[6]
    kind_of = lambda r: facts[r[0]][r[5]]["kind"] if r[5] else None
    liked = lambda r: kind_of(r) == "like"
    trap = lambda r: r[5] == "R1"
    stale = lambda r: bool(r[5]) and facts[r[0]][r[5]]["status"] != "current"
    fit_ok = lambda r: r[7] is True
    good = lambda r: r[7] is True and not r[6]  # suitable AND not built on a memory

    distinct = defaultdict(list)
    for key, g in groups.items():
        distinct[key.split("|")[2]].append(g["distinct"])

    L = ["# Benchmark 结果：带记忆的 AI 是不是只在记忆里打圈", "",
         f"{len(users)} 个用户 × {len(questions)} 个问题 × {len(ARMS)} 组 × {SAMPLES} 次，每次 {IDEAS} 个点子，"
         f"共 {len(rows)} 个点子。回答、评委都是 DeepSeek，存在同源偏差（见 SPEC.md 第 6 节）。", "",
         "## 总表", "",
         "| 组 | 打圈率 | 被喜好带跑 | 踩陷阱 | 被过时信息带跑 | 合适率 | 好点子率（合适且跳出记忆） | 点子种类数（满分 15） |",
         "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for arm in ARMS:
        d = statistics.mean(distinct[arm]) if distinct[arm] else 0
        L.append(f"| {arm} | {pct(share(arm, cited))} | {pct(share(arm, liked))} | {pct(share(arm, trap))} | "
                 f"{pct(share(arm, stale))} | {pct(share(arm, fit_ok))} | {pct(share(arm, good))} | {d:.1f} |")

    L += ["", "## 每个用户的打圈率", "", "| 用户 | " + " | ".join(ARMS) + " |", "| --- |" + " --- |" * len(ARMS)]
    for u in users:
        L.append(f"| {u['name']} | " + " | ".join(pct(share(arm, cited, u["id"])) for arm in ARMS) + " |")

    L += ["", "## 被哪一类信息带跑（占全部点子的比例）", "",
          "| 组 | " + " | ".join(KIND_NAMES[k] for k in KIND_ORDER) + " | 对不上人设的记忆 |",
          "| --- |" + " --- |" * (len(KIND_ORDER) + 1)]
    for arm in ARMS:
        cells = [pct(share(arm, lambda r, k=k: kind_of(r) == k)) for k in KIND_ORDER]
        cells.append(pct(share(arm, lambda r: r[6] and not r[5])))
        L.append(f"| {arm} | " + " | ".join(cells) + " |")

    # exposure: per fact, how often its memory got built on in B, grouped by kind x real exposure
    L += ["", "## 出现次数的影响（B 组）", "",
          "每条信息平均带出多少个点子，按“聊天里实际出现几次”分组。", "",
          "| 种类 | 出现 1 次 | 出现 2 次 | 出现 4 次以上 |", "| --- | --- | --- | --- |"]
    per_fact = defaultdict(int)
    for r in rows:
        if r[2] == "B_memory" and r[5]:
            per_fact[(r[0], r[5])] += 1
    for k in KIND_ORDER:
        cells = []
        for lo, hi in ((1, 1), (2, 3), (4, 99)):
            sel = [(uid, fid) for uid in facts for fid, f in facts[uid].items()
                   if f["kind"] == k and lo <= exposure.get((uid, fid), 0) <= hi]
            cells.append(f"{statistics.mean(per_fact[x] for x in sel):.1f}（{len(sel)} 条）" if sel else "-")
        L.append(f"| {KIND_NAMES[k]} | " + " | ".join(cells) + " |")

    lift = {u["id"]: share("B_memory", cited, u["id"]) - share("A_none", cited, u["id"]) for u in users}
    overall = statistics.mean(lift.values())
    n_users = sum(v >= 0.20 for v in lift.values())
    L += ["", "## 判定（标准事先写在 SPEC.md 第 1 节）", "",
          f"- 带记忆比不带记忆，打圈率平均高 {pct(overall)}；{n_users}/{len(users)} 个用户高出 20 个百分点以上。"
          f"→ **打圈{'成立' if overall >= 0.20 and n_users >= 4 else '不成立'}**"]
    for arm in ("C_memory_nudge", "D_memory_hot"):
        drop = statistics.mean(share("B_memory", cited, u["id"]) - share(arm, cited, u["id"]) for u in users)
        rec = drop / overall if overall > 0 else 0
        L.append(f"- {arm}：把多出来的打圈率降回去 {pct(rec)}。→ **{'补救有效' if rec >= 0.5 else '补救无效'}**")

    for arm in [a for a in ARMS if ARMS[a].get("widen")]:
        f, g = share(arm, fit_ok), share(arm, good)
        ok = f >= 0.70 and g >= 0.55
        L.append(f"- {arm}：合适率 {pct(f)}（标准 ≥ 70%），好点子率 {pct(g)}（标准 ≥ 55%）→ **{'达标' if ok else '未达标'}**")

    L += ["", "## 例子：第 1 个问题，不带记忆 vs 带记忆", ""]
    for u in users:
        L.append(f"**{u['name']}：{questions[0]}**")
        for arm in [a for a in ("A_none", "B_memory", "E1_widen") if a in ARMS]:
            L.append(f"- {arm}：")
            for r in [r for r in rows if r[0] == u["id"] and r[1] == 0 and r[2] == arm][:IDEAS]:
                tag = f"（来自记忆「{r[4]}」）" if r[6] else ""
                L.append(f"    - {r[3]}{tag}")
        L.append("")

    (RESULTS / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    rng = random.Random(0)
    with (RESULTS / "spotcheck.csv").open("w", encoding="utf-8") as f:
        f.write("user,arm,question,idea,judge_memory,human_memory\n")
        for r in rng.sample(rows, min(50, len(rows))):
            f.write(",".join(json.dumps(x, ensure_ascii=False)
                             for x in (by_user[r[0]]["name"], r[2], questions[r[1]], r[3], r[4])) + ",\n")
    print("\n".join(L))


STAGES = {"generate": stage_generate, "audit": stage_audit, "repair": stage_repair, "ingest": stage_ingest, "link": stage_link, "answer": stage_answer, "judge": stage_judge, "fit": stage_fit,
          "group": stage_group, "report": stage_report}


def main(argv: list[str]) -> int:
    RESULTS.mkdir(exist_ok=True)
    questions, llm = load_questions(), LLM()
    for name in argv or list(STAGES):
        STAGES[name](load_users(), questions, llm)  # reload: earlier stages write files later ones read
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
