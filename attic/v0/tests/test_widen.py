import json
from pathlib import Path

from widen import bench, hook
from widen.core import judge_intent, widen
from widen.llm import FakeLLM
from widen.memory import load_memories
from widen.similarity import novelty, similarity

EXAMPLE_MEMORY = Path(__file__).parents[1] / "examples" / "persona-lin" / "memory"
MEMORIES = ["每天吃一个苹果", "三年 Go 后端经验"]


def fake(**overrides):
    answers = {
        "intent": {"intent": "explore", "reason": "wants ideas"},
        "light": {"topics": [{"name": "苹果", "kind": "like"}, {"name": "Go 后端", "kind": "know"}]},
        "dark": {"topics": [{"name": "分布式追踪", "near": "Go 后端"}, {"name": "果园供应链", "near": "苹果"}]},
        "explore": {"ideas": [
            {"text": "做一个苹果品种图鉴网站", "area": "果园供应链"},          # close to memory
            {"text": "给小团队写一个轻量分布式追踪采样器", "area": "分布式追踪"},
            {"text": "做农产品冷链温度告警工具", "area": "果园供应链"},
        ]},
        "judge": {"picks": [{"index": 1, "fit": "会 Go", "memory": "三年 Go 后端经验"},
                            {"index": 2, "fit": "不用前端", "memory": None}]},
    }
    answers.update(overrides)
    return FakeLLM(answers)


def test_load_memories_reads_markdown_items():
    items = load_memories(EXAMPLE_MEMORY)
    assert "讨厌写前端 CSS" in items
    assert not any(i.startswith("#") for i in items)


def test_novelty_is_low_for_text_close_to_memory():
    assert similarity("每天吃一个苹果", "每天吃一个苹果") > 0.99
    assert novelty("做一个苹果品种图鉴网站", MEMORIES) < novelty("写一个分布式追踪采样器", MEMORIES)
    assert novelty("anything", []) == 1.0


def test_intent_failure_falls_back_to_do():
    def boom(system, user):
        raise RuntimeError("network down")
    assert judge_intent("帮我想想", FakeLLM({"intent": boom}))[0] == "do"


def test_plain_task_skips_the_pipeline():
    llm = fake(intent={"intent": "do", "reason": "clear task"})
    result = widen("把 panic 改成返回 error", MEMORIES, llm)
    assert result.intent == "do" and not result.picks
    assert [c[0] for c in llm.calls] == ["intent"]


def test_explorer_never_sees_memories_and_judge_does():
    llm = fake()
    result = widen("周末做什么项目", MEMORIES, llm, k=2, min_novelty=0.0)
    prompts = {task: user for task, _, user in llm.calls}
    assert "苹果" not in prompts["explore"].split("Unexplored areas")[0]  # question part only
    assert "三年 Go 后端经验" not in prompts["explore"]
    assert "三年 Go 后端经验" in prompts["judge"]
    assert [p.text for p in result.picks][:1] == ["做一个苹果品种图鉴网站"]
    assert result.picks[0].memory == "三年 Go 后端经验"


def test_novelty_filter_drops_ideas_close_to_memory():
    llm = fake()
    result = widen("周末做什么项目", MEMORIES, llm, k=2, min_novelty=0.9)
    judged = llm.calls[-1][2]
    assert "苹果品种图鉴" not in judged  # filtered out before the judge saw it
    assert len(result.candidates) == 3


def test_lit_topics_are_cached(tmp_path):
    llm = fake()
    widen("q", MEMORIES, llm, force=True, cache_dir=tmp_path, min_novelty=0)
    widen("q", MEMORIES, llm, force=True, cache_dir=tmp_path, min_novelty=0)
    assert [c[0] for c in llm.calls].count("light") == 1


def test_hook_passes_plain_tasks_through_silently():
    out = hook.main(json.dumps({"prompt": "修一下这个 bug"}), lambda: fake(intent={"intent": "do"}))
    assert out == ""


def test_hook_adds_context_for_idea_requests(tmp_path, monkeypatch):
    (tmp_path / "MEMORY.md").write_text("- 每天吃一个苹果\n", encoding="utf-8")
    monkeypatch.setenv("WIDEN_MEMORY", str(tmp_path))
    monkeypatch.setattr(hook, "CACHE_DIR", tmp_path / "cache")
    out = json.loads(hook.main(json.dumps({"prompt": "widen: 周末做什么"}), fake))
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "分布式追踪" in context and "at least half" in context


def test_hook_never_raises():
    assert hook.main("not json", fake) == ""


def test_count_distinct_counts_groups_and_leftovers():
    llm = FakeLLM({"group": {"groups": [[1, 2], [3]]}})
    assert bench.count_distinct(["a", "a'", "b", "c"], llm) == 3


def test_bench_runs_all_arms():
    llm = fake(answer={"ideas": ["做一个苹果图鉴", "写 Go 工具"]}, group={"groups": [[1], [2]]})
    rows = bench.run([{"scenario": "s", "question": "q"}], MEMORIES, llm, samples=1, k=2)
    scores = rows[0]["scores"]
    assert set(scores) == {"none", "memory", "widen"}
    assert scores["widen"]["intents"] == ["explore"]
    assert "| s | q | explore |" in bench.report(rows, 1)
