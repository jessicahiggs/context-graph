# context-graph

Turn a folder of markdown notes into a **knowledge graph** — the systems, models, datasets, people and metrics you write about, and the relationships between them — so Claude answers from your actual notes instead of guessing or grepping.

Created by [Jessica Higgs](https://github.com/jessicahiggs).

## The problem

Search finds files containing the word "evaluation."

A graph answers *"which agents depend on the eval harness, and which of them still read from the old context format"* — because it knows one note describes a system, that the system is evaluated by another, what it reads context from, and when that dependency was last changed.

Your notes already contain that graph. It's just trapped in prose.

## What you need

| Requirement | Why |
|---|---|
| **Claude** (Claude Code or claude.ai) | Extracts entities and relationships from your prose |
| **Python 3** | Parses the notes and stores the graph. Ships with macOS and Linux |
| **A folder of markdown notes** | Obsidian, Logseq, or plain `.md` files |

No API key, no token, no scheduled job, no network access. **Works on macOS, Linux and Windows.**

> [!Note]
> You may need to use `python` at start of command instead of `python3` depending on how your Windows system is configured.
>

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

## Try it first

A small sample vault ships with the repo, so you can see real output before pointing
this at your own notes:

```bash
python3 scripts/build_graph.py examples/sample-vault --out sample.json
python3 scripts/query_graph.py --graph sample.json --note "Architecture Overview" --hops 1
```

Six notes describing a fictional AI platform, wikilinked to each other. Enough to see
what the structural pass produces and how traversal works, without reading anything
of yours.

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
  {"name": "coding-agent", "type": "system"},
  {"name": "eval-harness", "type": "system"},
  {"name": "context-layer", "type": "system"},
  {"name": "hallucination-rate", "type": "metric"}
],
"relations": [
  {"source": "coding-agent", "target": "eval-harness", "type": "evaluated_by"},
  {"source": "coding-agent", "target": "context-layer", "type": "reads_context_from"},
  {"source": "eval-harness", "target": "hallucination-rate", "type": "reports", "date": "2026-06-02"}
]
```

Then queries run against the graph instead of your files:

```bash
python3 scripts/query_graph.py "which systems depend on the eval harness"
python3 scripts/query_graph.py --note "Architecture Overview" --hops 1
python3 scripts/query_graph.py --entity "context-layer" --hops 2
python3 scripts/query_graph.py --stats
```

## Why bother

- **No guessing which file to open** — one lookup returns the relevant slice
- **Less context burned** — only relevant facts are loaded, not whole documents
- **It persists** — built once, updated incrementally, instead of every session rediscovering the same facts
- **Cross-file questions get cheap** — "which components read from the context layer and which metrics they report" is a traversal, not a reading exercise

## Incremental by design

Re-run the structural pass whenever notes change. Files are hashed, so unchanged notes keep their extractions and only modified ones come back for a cheap top-up. `--rebuild` starts clean, and is only needed if you change which entity types you're tracking.

## Design notes

- **A wrong edge is worse than a missing one.** The skill instructs the model to extract only what a note actually states — mentioning two names in a sentence is not a relationship. Invented edges get retrieved later and believed.
- **Name normalisation matters more than it sounds.** "eval-harness", "the eval service" and "EvalHarness" must collapse to one entity or traversal silently breaks.
- **Decide the entity types before extracting.** An AI platform needs systems, models, datasets, metrics and owners. Research needs papers, authors and concepts. Generic extraction produces a graph that answers nothing well.
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
