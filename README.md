# Widen

**Your AI remembers you. Widen keeps that memory from boxing you in.**

[中文](README.zh-CN.md)

Give an assistant long-term memory and ask it for ideas. Most of what comes back is about your past. You
mentioned Japanese once, so every book it suggests is a Japanese textbook. You own a dog, so your weekend
project is a shedding log for the dog.

Widen is a plugin for [Mem0](https://github.com/mem0ai/mem0) that adds a fourth retrieval path, built like a
recommender system's exploration channel. Plain questions go through untouched. When you ask for ideas, Widen
finds directions you haven't explored yet, checks them against your real limits, and hands those to the model
**instead of** your memories.

---

## Before / after

These are real outputs from our benchmark. The users are fictional and the answers are unedited first samples,
translated from Chinese. **Plain memory** is Mem0 with its standard retrieval. **Widen** is the plugin.

### "What should I read next?" (a medical grad student who once said he'd like to get back to Japanese)

| Plain memory | Widen |
| --- | --- |
| *Nihongo Sō-matome N5* grammar, to build on the kana you just learned | *Nineteen Eighty-Four* in print: a tense story to read at bedtime instead of scrolling |
| A collection of short Japanese fairy tales with furigana | A collection of short mystery stories, one complete case per night after a night shift |
| *Yotsuba&!*, an easy, dialogue-heavy manga | *The Tale of Genji* in translation, as slow, quiet reading before sleep |
| The *Nihongo 1000 Knock* speaking and listening drills | *On the Origin of Species*, a few pages at a time before your daytime nap |
| Hoshi Shin'ichi's short stories, at moderate Japanese difficulty | A book of essays on your nightstand, one or two a night |

**All five on the left grow out of one remembered sentence.**

### "Any ideas for a small weekend project?" (a freelance illustrator)

| Plain memory | Widen |
| --- | --- |
| A photo book for grandma, scanned and laid out on your phone ← *going home to care for grandma* | A short photo series of light and shadow by your window |
| A 15-second video of your food photos ← *often posts food photos* | An origami or knotted-cord piece from materials at home, done sitting down |
| A seasonal sticker set of the little fox from the picture book ← *current client job* | A photo-and-caption piece about the street vendors downstairs |
| An illustrated list of hometown snacks ← *hometown is Guizhou* | Watch the *Apu Trilogy* over a few sittings and jot down notes |
| A slow-motion shot of pouring craft beer ← *likes craft beer* | Turn an old box or old clothes into a small storage piece, cheaply and quietly for the roommate |

### "Any ideas for a small weekend project?" (a small-town physics teacher)

| Plain memory | Widen |
| --- | --- |
| A list of old comedy routines for the uncle's folk-art troupe ← *uncle runs the troupe* | Grow one or two easy greens or herbs on the balcony with kitchen-scrap compost |
| A daily shedding log for the dog ← *has a dog* | A few low-maintenance indoor plants, potted in jars you already have |
| A quiz card on one word in a Tang poem ← *asked about it once* | Sketch a plan for a tiny balcony garden, then try it with a few real pots |
| A night video of the empty county-town streets ← *lives in a county town* | Walk the wetlands at the edge of town, photograph and identify sedges, and make a small field note |
| A snack list for watching football ← *watches the Premier League* | Sort out one drawer or corner and label everything |

---

## Results

We gave 5 fictional users 60 chat sessions each and let Mem0 extract their memories. Each user then asked 10
open questions ("weekend project", "what to learn", "a side hustle", "a gift idea" …), with 3 samples and 5 ideas
per answer, giving 750 ideas per arm. A judge model labelled every idea for two things: whether it grows out of a
specific memory, and whether it actually suits the person, checked against their true profile.

| Arm | Circling (idea grows out of a memory) | Fit | Good ideas (fit **and** not from memory) |
| --- | --- | --- | --- |
| No memory | 7% | 47% | 43% |
| Plain memory (Mem0) | 52% | 69% | 33% |
| Memory + "don't limit yourself to the user's past" | 38% | 69% | 44% |
| Memory + temperature 1.3 | 51% | 67% | 33% |
| **Memory + Widen** | **26%** | **80%** | **58%** |

- Memory makes ideas fit better (47% → 69%). It also halves how many escape the user's past.
- Telling the model to be diverse, or raising the temperature, doesn't fix that (independently found by
  [MemBubble](https://arxiv.org/abs/2610.25127), which measured the same narrowing across five memory systems).
- Widen keeps the fit, and lifts good ideas from 33% to 58%. Ideas driven by a mere *like* drop from 9% to 2%.
- Plain questions are untouched. On [LoCoMo](https://github.com/snap-research/locomo)'s 1,986 fact-recall
  questions, Widen sent only 0.65% down the exploration path, so recall accuracy can drop by at most 0.65 points.

Full report: [`benchmark/REPORT-v2d.md`](benchmark/REPORT-v2d.md). Setup and pre-registered criteria:
[`benchmark/SPEC.md`](benchmark/SPEC.md).

---

## How it works

Widen treats "suggest something new" like a recommender treats "what to show next": first search by the
question, then personalise.

```
question ─► intent: plain task? ──yes──► Mem0's results, unchanged
               │ no (wants ideas)
               ▼
   recall by the QUESTION   search phrases → Wikipedia vital articles (6,198 topics)
                            + where readers of those pages click next (Wikipedia clickstream)
   coarse rank (formula)    question relevance + profile match + λ·novelty − genericness
   fine rank + filter (LLM) how appealing and usable for this person; drop what their hard limits rule out
   rerank                   one per topic area, one slot kept for the most novel candidate that passed
   bridge + final check     one concrete direction per topic, re-checked against the limits
               ▼
   directions only ─► your model writes the answer
```

- **Memories light up topics; they don't pick directions.** Topics you already touch, and near-copies of them,
  are excluded.
- **Hard limits** (health, time, money, abilities, dislikes, place) are distilled once per user from all
  memories and cached.
- **Why directions only:** handing the model your memories as well pulled a third of its ideas back to them
  (good ideas 45% instead of 56–58%).
- **Cost:** a plain question costs 1 extra model call. An idea request costs 3: intent, fine rank, and bridge,
  plus cached per-user work the first time.

Design notes: [`SPEC.md`](SPEC.md) · [`docs/recsys-to-memory.md`](docs/recsys-to-memory.md) ·
[`docs/granularity.md`](docs/granularity.md) · [`docs/related-work.md`](docs/related-work.md)

---

## Quick start

> Early research code, not on PyPI yet.

```bash
git clone https://github.com/destire-mio/widen.git && cd widen
python -m venv .venv && .venv/bin/pip install -e . mem0ai ollama spacy fastembed
.venv/bin/python -m spacy download en_core_web_sm
ollama pull nomic-embed-text
echo "WIDEN_API_KEY=sk-..." > .env          # any OpenAI-compatible API; default model deepseek-flash
.venv/bin/python -m widen.table.vital --level 4                    # topic table, once
# download clickstream-enwiki-YYYY-MM.tsv.gz from https://dumps.wikimedia.org/other/clickstream/
.venv/bin/python -m widen.table.clickstream data/clickstream/clickstream-enwiki-YYYY-MM.tsv.gz
```

```python
from mem0 import Memory
from widen.adapters.mem0 import WidenMemory

memory = WidenMemory(Memory.from_config(config))     # everything else is passed through to Mem0
memory.search("Any ideas for a small weekend project?", filters={"user_id": "alice"})
```

---

## Status and limits

Please read this before quoting the numbers.

- **Held-out test pending.** The winning setup was chosen after several rounds on the same 5 users and
  10 questions. It still has to pass on users and questions we never looked at while developing.
- **Small margins.** With 750 ideas per arm, the 95% interval is about ±3.5 points. 58% clears the 55% bar, but
  only just.
- **The judge is the same model family as the answerer** (DeepSeek). A human spot check passed on round 1; it
  hasn't been repeated for this round yet.
- **Synthetic users.** Their histories are generated from persona sheets, and the questions are in Chinese.
- The topic table is English Wikipedia. A few personas' details get garbled in Mem0's English memories.

## License

MIT
