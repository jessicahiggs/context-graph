# context-graph

Turn a folder of markdown notes into a **knowledge graph** — people, companies, projects and the relationships between them — so Claude answers from your actual notes instead of guessing or grepping.

Created by [Jessica Higgs](https://github.com/jessicahiggs).

## The problem

Search finds files containing the word "Stripe."

A graph answers *"who do I know that could introduce me to someone at Stripe"* — because it knows one note describes a person, that the person works at Stripe, when you last spoke, and which other contacts overlap.

Your notes already contain that graph. It's just trapped in prose.

## What you need

| Requirement | Why |
|---|---|
| **Claude** (Claude Code or claude.ai) | Extracts entities and relationships from your prose |
| **Python 3** | Parses the notes and stores the graph. Ships with macOS and Linux |
| **A folder of markdown notes** | Obsidian, Logseq, or plain `.md` files |

No API key, no token, no scheduled job, no network access. **Works on macOS, Linux and Windows.**

## Install

Download this repo and copy the `context-graph` folder into your Claude skills directory:

```bash
git clone https://github.com/jessicahiggs/context-graph.git
mkdir -p ~/.claude/skills
cp -r context-graph ~/.claude/skills/
```

On claude.ai: zip the `context-graph` folder — with `SKILL.md` at the top level inside it — and upload under Settings → Capabilities → Skills.

Then say:

> build a knowledge graph from my notes in ~/Documents/vault

## How it works

Two passes, kept separate on purpose:

**1. Structural** — a script walks your notes and extracts what can be read deterministically: files, wikilinks, tags, headings, backlinks. Free, instant, re-runnable.

```bash
python3 scripts/build_graph.py ~/Documents/vault --out graph.json
```

```
notes: 76  (unchanged 0, new/changed 76)
wikilink edges resolved: 60
awaiting model extraction: 76
```

**2. Semantic** — Claude reads the notes and extracts entities and relationships, writing them back into `graph.json`. This is the part a script can't do.

```json
"entities": [
  {"name": "Ekow Essel", "type": "person"},
  {"name": "Stripe", "type": "company"}
],
"relations": [
  {"source": "Ekow Essel", "target": "Stripe", "type": "works_at"},
  {"source": "Jessica", "target": "Ekow Essel", "type": "spoke_with", "date": "2026-07-24"}
]
```

Then queries run against the graph instead of your files:

```bash
python3 scripts/query_graph.py "who do I know at Stripe"
python3 scripts/query_graph.py --note "Job Search" --hops 1
python3 scripts/query_graph.py --entity "Stripe" --hops 2
python3 scripts/query_graph.py --stats
```

## Why bother

- **No guessing which file to open** — one lookup returns the relevant slice
- **Less context burned** — only relevant facts are loaded, not whole documents
- **It persists** — built once, updated incrementally, instead of every session rediscovering the same facts
- **Cross-file questions get cheap** — "which of my contacts work at companies where I have something open" is a traversal, not a reading exercise

## Incremental by design

Re-run the structural pass whenever notes change. Files are hashed, so unchanged notes keep their extractions and only modified ones come back for a cheap top-up. `--rebuild` starts clean, and is only needed if you change which entity types you're tracking.

## Design notes

- **A wrong edge is worse than a missing one.** The skill instructs the model to extract only what a note actually states — mentioning two names in a sentence is not a relationship. Invented edges get retrieved later and believed.
- **Name normalisation matters more than it sounds.** "JP Morgan", "JPMorgan Chase" and "JPM" must collapse to one entity or traversal silently breaks.
- **Decide the entity types before extracting.** A job search needs people, companies, roles, referrals. Research needs papers, authors, concepts. Generic extraction produces a graph that answers nothing well.
- **Wikilinks are free edges.** Obsidian vaults start with half the graph already drawn, which is why the structural pass runs first.

## Limitations

- **The first build reads every note once** — that's the expensive pass. Updates after that are cheap.
- **Graph quality follows note quality.** Vague prose makes a vague graph.
- **Markdown only** — PDFs, images and databases are ignored.
- **It never writes to your notes.** The only file it modifies is `graph.json`.

## Files

- `SKILL.md` — the skill: setup interview, extraction rules, query flow, guardrails
- `scripts/build_graph.py` — structural pass, incremental via content hashing
- `scripts/query_graph.py` — search, traversal and coverage stats

## License

MIT — see [LICENSE](LICENSE).
