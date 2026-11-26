# Data

| File | What | Source and license |
| --- | --- | --- |
| `vital-l4.json` | 6,198 Wikipedia "Vital articles" (level 4, without people, geography and history): title, section path, short description, Chinese title | [English Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Vital_articles), text under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| `vital-l4.npy` | One vector per article (`nomic-embed-text`, normalised) | Derived from the file above |

Rebuild both with `python -m widen.table.vital --level 4`.

The click graph (`clicks-l4.npz`) is not committed. Build it from the [Wikipedia clickstream](https://meta.wikimedia.org/wiki/Research:Wikipedia_clickstream) dump with `python -m widen.table.clickstream <clickstream-enwiki-YYYY-MM.tsv.gz>`. Without it, Widen falls back to the section tree and vectors.
