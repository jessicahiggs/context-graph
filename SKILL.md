---
name: context-graph
description: Build and query a knowledge graph from someone's own markdown notes — extracting people, companies, projects and the relationships between them, so answers are grounded in their actual notes instead of guessed or retrieved by keyword. Use this when a user wants to make an Obsidian vault or notes folder queryable, asks questions spanning many notes ("who do I know at X", "which contacts relate to this project"), wants Claude to stop re-reading whole files to answer, or asks to build a knowledge graph, context layer, or semantic index over their notes. Runs a structural pass with a script, then a model pass that extracts entities and relationships, and answers later questions from the graph.
metadata:
  author: Jessica Higgs (@jessicahiggs)
  repository: https://github.com/jessicahiggs/context-graph
---

# Context Graph

Turns a folder of markdown into a queryable graph of **entities** (people, companies, projects, concepts) and **relationships** between them, then answers questions by retrieving the relevant slice instead of reading whole files.

**Two passes, deliberately separated:**

| Pass | Who does it | What it produces |
|---|---|---|
| **Structural** | `build_graph.py` | files, wikilinks, tags, headings, backlinks — deterministic, free, instant |
| **Semantic** | you, the model | entities and relationships extracted from prose |

The structural pass is cheap and re-runnable. The semantic pass costs model calls, so it is incremental: only notes whose content changed are re-extracted.

## Step 0 — Check before promising

1. **`python3`** — `command -v python3`. Ships with macOS and Linux; on Windows it may be `python`.
2. **A notes directory** the user can point at.

No API key, no token, no scheduled job, no network access. Works on macOS, Linux and Windows.

## Step 1 — Ask what matters

Two questions, no more:

1. **Where are the notes?** A path. Confirm it exists before running anything.
2. **What do they actually want to ask it?** This is the important one — it decides which entity types are worth extracting. Someone documenting an AI platform wants systems, models, datasets, metrics and owners. Someone doing research wants papers, authors and concepts. **Do not extract generic "entities"; extract the kinds they will ask about.**

Agree a small type list, 4–6 at most. More types make the graph noisier, not richer.

## Step 2 — Structural pass

```bash
python3 scripts/build_graph.py "<notes_dir>" --out graph.json
```

Reports note count, resolved wikilink edges, and how many notes await extraction. Safe to re-run any time; it preserves extractions for unchanged notes.

## Step 3 — Semantic pass (this is your job)

Read `graph.json`. For each note where `"extracted": false`, open the file at `root` + `path`, then write back into that note's record:

```json
"entities": [
  {"name": "coding-agent", "type": "system"},
  {"name": "eval-harness", "type": "system"},
  {"name": "hallucination-rate", "type": "metric"}
],
"relations": [
  {"source": "coding-agent", "target": "eval-harness", "type": "evaluated_by"},
  {"source": "eval-harness", "target": "hallucination-rate", "type": "reports", "date": "2026-06-02"}
],
"extracted": true
```

Rules that keep the graph trustworthy:

- **Extract only what the note states.** If a note says a service "runs against the eval harness nightly," that is `evaluated_by`. If it merely mentions two systems in one sentence, that is not a relationship. **Never infer a relationship to make the graph look richer** — a wrong edge is worse than a missing one, because it will be retrieved and believed later.
- **Normalise names.** "eval-harness", "the eval service" and "EvalHarness" must become one entity, or traversal breaks. Keep the fullest form as `name`.
- **Reuse types from the agreed list.** A type used once is noise.
- **Dates in relations are valuable** — they let the user ask "what changed since the June migration."
- **Batch the work.** Read many notes, then write `graph.json` once. Do not rewrite the file per note.
- **Say what it cost.** Tell the user how many notes you extracted and roughly how long a full rebuild takes, so a large vault is not a surprise.

Set `"extracted": true` only for notes you genuinely processed.

## Step 4 — Answer from the graph

```bash
python3 scripts/query_graph.py "which systems depend on the eval harness"   # search
python3 scripts/query_graph.py --note "Architecture Overview" --hops 1     # subgraph around a note
python3 scripts/query_graph.py --entity "context-layer" --hops 2          # traverse from an entity
python3 scripts/query_graph.py --stats                        # coverage
```

**Query the graph first, open files second.** The point is to avoid reading whole notes. Use the returned subgraph to answer; open a file only when the graph shows a note is relevant but lacks the detail needed.

## Step 5 — Keeping it current

Re-run Step 2 whenever notes change; unchanged notes keep their extractions and only changed ones come back as `extracted: false` for a cheap top-up. `--rebuild` discards everything and starts over — only use it when the entity type list changes.

## Guardrails

- **Never invent entities or relationships.** Only what the notes say.
- **Never write to the user's notes.** This skill reads them and writes only `graph.json`.
- **Personal notes are private.** Do not summarise their contents beyond what is needed to answer, and do not send them anywhere.
- **Be honest about coverage.** If `--stats` shows 40 of 300 notes extracted, say so before answering, rather than implying the graph is complete.
- **A graph is not a search engine.** If someone asks something the graph cannot answer, say so and fall back to reading files — don't force a bad traversal.

## Limitations

- **First build is the expensive one** — every note is read once. Incremental updates after that are cheap.
- **Quality depends on the notes.** Vague prose produces a vague graph. Vaults with existing wikilinks start with a real head start, since those edges come free.
- **Markdown only.** PDFs, images and databases are ignored.
