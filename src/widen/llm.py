"""LLM access. Every call asks for a JSON object and names its task, so tests can fake it."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def read_env_file(*paths: Path) -> dict[str, str]:
    """Parse simple KEY=VALUE lines. Earlier paths win."""
    values: dict[str, str] = {}
    for path in reversed(paths):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


class LLM:
    """OpenAI-compatible chat client (DeepSeek by default).

    Settings come from ./.env, then the project's .env, then the shell environment:
    WIDEN_API_KEY (or DEEPSEEK_API_KEY), WIDEN_BASE_URL, WIDEN_MODEL, WIDEN_THINKING.

    Default model: deepseek-flash with thinking DISABLED. DeepSeek turns thinking on by default for it; thinking
    costs extra output tokens, is slower, and ignores temperature (the benchmark's high-temperature arm needs it).
    The old name "deepseek-chat" (non-thinking v4-flash) was announced for retirement on 2026-07-24.
    """

    def __init__(self, model: str | None = None, base_url: str | None = None,
                 api_key: str | None = None, temperature: float = 0.7):
        from openai import OpenAI

        env = read_env_file(Path.cwd() / ".env", PROJECT_ROOT / ".env")

        def pick(*names: str, default: str | None = None) -> str | None:
            for name in names:
                if env.get(name):
                    return env[name]
            for name in names:
                if os.getenv(name):
                    return os.getenv(name)
            return default

        key = api_key or pick("WIDEN_API_KEY", "DEEPSEEK_API_KEY")
        if not key:
            raise RuntimeError("No API key: put WIDEN_API_KEY=... in a .env file (see .env.example).")
        self.model = model or pick("WIDEN_MODEL", default="deepseek-flash")
        self.thinking = pick("WIDEN_THINKING", default="disabled")
        self.served: set[str] = set()   # model versions the API reported actually serving
        self.temperature = temperature
        self.client = OpenAI(api_key=key, base_url=base_url or pick("WIDEN_BASE_URL", default="https://api.deepseek.com"),
                             timeout=90, max_retries=2)

    def json(self, task: str, system: str, user: str, temperature: float | None = None, tries: int = 3) -> dict:
        """One JSON-mode call. DeepSeek returns blank content when the JSON it generated was invalid,
        so blank or unparsable answers are retried before giving up."""
        extra = {"thinking": {"type": self.thinking}} if "deepseek" in self.model else None
        last: Exception | None = None
        for _ in range(tries):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                response_format={"type": "json_object"},
                temperature=self.temperature if temperature is None else temperature,
                extra_body=extra,
            )
            if getattr(response, "model", None):
                self.served.add(response.model)
            content = (response.choices[0].message.content or "").strip()
            if not content:
                last = ValueError("blank JSON content")
                continue
            try:
                return json.loads(content)
            except json.JSONDecodeError as exc:
                last = exc
        raise last or ValueError("no answer")


class FakeLLM:
    """Test double: answers by task name with a fixed dict or a function of (system, user)."""

    def __init__(self, answers: dict[str, dict | Callable[[str, str], dict]]):
        self.answers = answers
        self.calls: list[tuple[str, str, str]] = []

    def json(self, task: str, system: str, user: str, temperature: float | None = None) -> dict:
        self.calls.append((task, system, user))
        answer = self.answers[task]
        return answer(system, user) if callable(answer) else answer
