"""Load memories as a flat list of short text items."""
from __future__ import annotations

import re
from pathlib import Path

LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")


def _items_from_markdown(text: str) -> list[str]:
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)  # frontmatter
    items = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line = LINK.sub(r"\1", line).lstrip("-*0123456789. ").strip()
        if line:
            items.append(line)
    return items


def load_memories(path: str | Path) -> list[str]:
    """A file, or a folder of .md files (e.g. a Claude Code memory folder with MEMORY.md)."""
    path = Path(path).expanduser()
    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(path.glob("*.md"))
    else:
        raise FileNotFoundError(path)
    items: list[str] = []
    for file in files:
        items.extend(_items_from_markdown(file.read_text(encoding="utf-8")))
    return list(dict.fromkeys(items))  # drop exact duplicates, keep order


def mem0_memories(mem0, user_id: str) -> list[str]:
    """Read all memories of one user from a mem0 `Memory` / `MemoryClient` object."""
    result = mem0.get_all(user_id=user_id)
    rows = result.get("results", []) if isinstance(result, dict) else result
    return [row["memory"] for row in rows if row.get("memory")]
