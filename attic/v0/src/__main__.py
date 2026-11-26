"""Command line: python -m widen ask | bench | hook"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import bench
from .core import widen
from .hook import CACHE_DIR, main as hook_main
from .llm import LLM
from .memory import load_memories

KIND_LABEL = {"like": "喜欢", "know": "懂", "have": "有资源", "dislike": "讨厌"}


def print_result(result) -> None:
    print(f"意图: {result.intent}  ({result.intent_reason})")
    if result.intent != "explore":
        print("这是一个明确的任务，Widen 不介入。")
        return
    print("\n记忆点亮的话题:")
    for t in result.lit:
        print(f"  - {t.get('name')} [{KIND_LABEL.get(t.get('kind'), t.get('kind'))}]")
    print("\n旁边没去过的话题:")
    for t in result.dark:
        print(f"  - {t.get('name')}  (挨着: {t.get('near')})")
    print("\n建议:")
    for n, idea in enumerate(result.picks, 1):
        used = f"用了记忆「{idea.memory}」" if idea.memory else "没用记忆"
        print(f"  {n}. {idea.text}\n     适合原因: {idea.fit}  [{used}]  新颖度 {idea.novelty}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="widen")
    sub = parser.add_subparsers(dest="command", required=True)

    ask = sub.add_parser("ask", help="answer one question with Widen")
    ask.add_argument("question")
    ask.add_argument("--memory", required=True, help="memory file or folder")
    ask.add_argument("--force", action="store_true", help="skip the intent check and always explore")
    ask.add_argument("--json", action="store_true", help="print raw JSON")

    b = sub.add_parser("bench", help="measure memory side effects: none vs memory vs widen")
    b.add_argument("--memory", required=True)
    b.add_argument("--questions", required=True, help="JSON list of {scenario, question}")
    b.add_argument("--samples", type=int, default=3)
    b.add_argument("--out", help="write the markdown report here; raw JSON goes next to it")

    sub.add_parser("hook", help="Claude Code UserPromptSubmit hook (reads the event from stdin)")

    args = parser.parse_args(argv)
    if args.command == "hook":
        out = hook_main(sys.stdin.read(), LLM)
        if out:
            print(out)
        return 0

    memories = load_memories(args.memory)
    llm = LLM()
    if args.command == "ask":
        result = widen(args.question, memories, llm, force=args.force, cache_dir=CACHE_DIR)
        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=1))
        else:
            print_result(result)
        return 0

    rows = bench.run(bench.load_questions(args.questions), memories, llm, args.samples, cache_dir=CACHE_DIR)
    text = bench.report(rows, args.samples)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        Path(args.out).with_suffix(".json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
