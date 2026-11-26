"""Build the topic table: Wikipedia Vital articles (level 3 = 1,000 articles) with short descriptions, Chinese titles and vectors.

This replaces Google's interest-cluster table (761 clusters, not public). Run once:
    python -m widen.table.vital [--level 3]
Writes data/vital-l<level>.json (title, section path, short description, Chinese title) and data/vital-l<level>.npy (vectors).
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "data"
API = "https://en.wikipedia.org/w/api.php"
UA = "widen-research/0.1 (open-source research tool)"
EMBED_MODEL = "nomic-embed-text"
SKIP_PREFIXES = ("File:", "Image:", "Category:", "Wikipedia:", "WP:", "Template:", "Help:", "Portal:", "User:", ":")


def api(params: dict, tries: int = 6) -> dict:
    """GET the MediaWiki API, backing off on 429 (Wikipedia rate-limits bursts)."""
    import urllib.error
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json", "formatversion": 2})
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == tries - 1:
                raise
            wait = float(e.headers.get("Retry-After") or 2 ** (attempt + 1))
            print(f"  rate limited, waiting {wait:.0f}s", flush=True)
            time.sleep(wait)


SKIP_ROOTS = ("People", "Biographies", "Geography", "History")  # rarely a direction for an idea
SKIP_PAGES = ("Draft", "draft", "Removed", "Article alerts", "Candidates")


def level_pages(level: int) -> list[str]:
    """Level 1-3 are single pages; level 4+ is split into subpages (redirects, drafts and skipped roots left out)."""
    root = f"Wikipedia:Vital articles/Level {level}"
    if level <= 3:
        return [root]
    out = api({"action": "query", "list": "allpages", "apprefix": f"Vital articles/Level {level}/",
               "apnamespace": 4, "aplimit": 500, "apfilterredir": "nonredirects"})
    pages = []
    for p in out["query"]["allpages"]:
        sub = p["title"].split(f"Level {level}/", 1)[1]
        if sub and not any(x in sub for x in SKIP_PAGES) and sub.split("/")[0] not in SKIP_ROOTS:
            pages.append(p["title"])
    return pages


def parse_wikitext(text: str) -> list[dict]:
    """Every list line's first article link, with the headings above it as its section path."""
    rows, path = [], []
    for line in text.splitlines():
        h = re.match(r"^(=+)\s*(.*?)\s*=+\s*$", line)
        if h:
            depth = len(h.group(1)) - 1
            name = re.sub(r"<[^>]+>|\(.*?\)|\[\[|\]\]|'''|''", "", h.group(2)).strip()
            path = path[: depth - 1] + [name]
            continue
        if not line.lstrip().startswith(("#", "*")):
            continue
        for target in re.findall(r"\[\[([^\]|#]+)", line):
            target = target.strip()
            if target and not target.startswith(SKIP_PREFIXES):
                rows.append({"title": target.replace("_", " "), "section": " / ".join(p for p in path if p)})
                break
    seen, unique = set(), []
    for r in rows:
        if r["title"] not in seen:
            seen.add(r["title"])
            unique.append(r)
    return unique


def descriptions(titles: list[str]) -> dict[str, dict]:
    """Short description + Chinese title per article, 50 titles per request (fewer requests than extracts)."""
    out = {}
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        res = api({"action": "query", "prop": "pageprops|langlinks", "ppprop": "wikibase-shortdesc",
                   "lllang": "zh", "lllimit": "max", "redirects": 1, "titles": "|".join(batch)})
        q = res.get("query", {})
        back = {r["to"]: r["from"] for r in q.get("redirects", [])}
        norm = {n["to"]: n["from"] for n in q.get("normalized", [])}
        for page in q.get("pages", []):
            title = page.get("title", "")
            original = back.get(title, title)
            original = norm.get(original, original)
            zh = next((l.get("title", "") for l in page.get("langlinks", []) if l.get("lang") == "zh"), "")
            out[original] = {"lead": page.get("pageprops", {}).get("wikibase-shortdesc", ""), "zh": zh}
        print(f"  {min(i + 50, len(titles))}/{len(titles)}", flush=True)
        time.sleep(1.5)
    return out


def embed(texts: list[str], prefix: str = "search_document: ") -> "list[list[float]]":
    import ollama
    vectors = []
    for i in range(0, len(texts), 64):
        vectors += ollama.embed(model=EMBED_MODEL, input=[prefix + t for t in texts[i:i + 64]])["embeddings"]
    return vectors


def build(level: int = 3) -> Path:
    import numpy as np
    rows = []
    for page in level_pages(level):
        text = api({"action": "parse", "page": page, "prop": "wikitext", "redirects": 1})["parse"]["wikitext"]
        sub = page.split(f"Level {level}/", 1)[1] if f"Level {level}/" in page else ""
        for r in parse_wikitext(text):
            r["section"] = " / ".join(x for x in (sub, r["section"]) if x)
            rows.append(r)
        time.sleep(1.0)
    seen, unique = set(), []
    for r in rows:
        if r["title"] not in seen and r["section"].split(" / ")[0] not in SKIP_ROOTS:
            seen.add(r["title"])
            unique.append(r)
    rows = unique
    print(f"level {level}: {len(rows)} articles", flush=True)
    info = descriptions([r["title"] for r in rows])
    for r in rows:
        r.update(info.get(r["title"], {"lead": "", "zh": ""}))
    vectors = np.array(embed([f"{r['title']}: {r['lead']}" for r in rows]), dtype=np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    DATA.mkdir(exist_ok=True)
    out = DATA / f"vital-l{level}.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding="utf-8")
    np.save(DATA / f"vital-l{level}.npy", vectors)
    print(f"wrote {out} and vectors {vectors.shape}", flush=True)
    return out


def load(level: int = 3):
    import numpy as np
    rows = json.loads((DATA / f"vital-l{level}.json").read_text(encoding="utf-8"))
    return rows, np.load(DATA / f"vital-l{level}.npy")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", type=int, default=3)
    build(ap.parse_args().level)
