#!/usr/bin/env python3
"""
context-graph — retrieve the relevant slice of the graph for a question.

Returns a compact subgraph rather than whole notes, so only the facts that matter
enter the model's context.

Usage:
    python3 query_graph.py "which systems depend on the eval harness"   # search
    python3 query_graph.py --entity "context-layer" --hops 2            # traverse from an entity
    python3 query_graph.py --note "Architecture Overview.md" --hops 1   # traverse from a note
    python3 query_graph.py --stats                            # what's in the graph
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

STOP = set("""a an the and or of in on at to for with from by is are was were be been
this that these those i me my we our you your it its as if then than so but not no
do does did have has had can could would should will just about into over under""".split())


def load(path: str) -> dict:
    if not os.path.exists(path):
        print(f"error: {path} not found — run build_graph.py first", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def tokens(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9][a-z0-9'-]+", s.lower()) if w not in STOP and len(w) > 2}


def entity_index(graph: dict):
    """entity name -> {note_ids}, plus the entity records themselves."""
    idx = defaultdict(set)
    records = {}
    for n in graph["notes"]:
        for e in n.get("entities", []):
            name = e.get("name")
            if not name:
                continue
            key = name.lower()
            idx[key].add(n["id"])
            r = records.setdefault(key, {"name": name, "type": e.get("type", "unknown"), "notes": set()})
            r["notes"].add(n["id"])
        # note titles are entities too
        idx[n["title"].lower()].add(n["id"])
    return idx, records


def relations_for(graph: dict, names: set):
    out = []
    for n in graph["notes"]:
        for r in n.get("relations", []):
            src, tgt = str(r.get("source", "")).lower(), str(r.get("target", "")).lower()
            if src in names or tgt in names:
                out.append({**r, "note": n["id"]})
    return out


def search(graph: dict, question: str, limit: int):
    q = tokens(question)
    idx, records = entity_index(graph)

    # entities whose name overlaps the question
    hits = {k: v for k, v in records.items() if tokens(v["name"]) & q}

    scored = []
    for n in graph["notes"]:
        hay = tokens(n["title"]) | set(n.get("tags", [])) | tokens(" ".join(n.get("headings", [])))
        hay |= {e.get("name", "").lower() for e in n.get("entities", [])}
        score = len(q & hay) * 3
        score += sum(1 for e in n.get("entities", []) if tokens(e.get("name", "")) & q) * 2
        for r in n.get("relations", []):
            if tokens(str(r.get("source", ""))) & q or tokens(str(r.get("target", ""))) & q:
                score += 2
        if score:
            scored.append((score, n))
    scored.sort(key=lambda x: -x[0])

    print(f"# question: {question}\n")
    if hits:
        print("## matched entities")
        for k, v in list(hits.items())[:20]:
            print(f"- {v['name']} ({v['type']}) — in {len(v['notes'])} note(s)")
        print()
        rels = relations_for(graph, set(hits))
        if rels:
            print("## relationships")
            for r in rels[:40]:
                print(f"- {r.get('source')} —[{r.get('type','related')}]→ {r.get('target')}   ({r['note']})")
            print()
    print("## most relevant notes")
    for score, n in scored[:limit]:
        ents = ", ".join(e.get("name", "") for e in n.get("entities", [])[:8])
        print(f"- {n['id']}  (score {score})")
        if ents:
            print(f"    entities: {ents}")
        if n.get("links_resolved"):
            print(f"    links: {', '.join(n['links_resolved'][:8])}")
    if not scored:
        print("(nothing matched — the graph may not be extracted yet; see SKILL.md)")


def traverse(graph: dict, seed_note: str, hops: int):
    notes = {n["id"]: n for n in graph["notes"]}
    match = seed_note if seed_note in notes else None
    if not match:
        for nid, n in notes.items():
            if n["title"].lower() == seed_note.lower() or nid.lower().endswith(seed_note.lower()):
                match = nid
                break
    if not match:
        print(f"error: no note matching {seed_note!r}", file=sys.stderr)
        sys.exit(1)

    seen, frontier = {match}, {match}
    for _ in range(hops):
        nxt = set()
        for nid in frontier:
            n = notes[nid]
            nxt |= set(n.get("links_resolved", [])) | set(n.get("backlinks", []))
        frontier = nxt - seen
        seen |= frontier

    print(f"# subgraph from {match}, {hops} hop(s) — {len(seen)} notes\n")
    for nid in sorted(seen):
        n = notes[nid]
        print(f"- {nid}")
        if n.get("entities"):
            print(f"    entities: {', '.join(e.get('name','') for e in n['entities'][:10])}")
        for r in n.get("relations", [])[:6]:
            print(f"    {r.get('source')} —[{r.get('type','related')}]→ {r.get('target')}")


def stats(graph: dict):
    notes = graph["notes"]
    ents = [e for n in notes for e in n.get("entities", [])]
    rels = [r for n in notes for r in n.get("relations", [])]
    by_type = defaultdict(int)
    for e in ents:
        by_type[e.get("type", "unknown")] += 1
    print(f"root:      {graph['root']}")
    print(f"built:     {graph['built']}")
    print(f"notes:     {len(notes)}")
    print(f"extracted: {sum(1 for n in notes if n.get('extracted'))} / {len(notes)}")
    print(f"edges:     {sum(len(n.get('links_resolved', [])) for n in notes)} wikilinks")
    print(f"entities:  {len(ents)}")
    for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"   {t}: {c}")
    print(f"relations: {len(rels)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?")
    ap.add_argument("--graph", default="graph.json")
    ap.add_argument("--entity")
    ap.add_argument("--note")
    ap.add_argument("--hops", type=int, default=1)
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()

    g = load(a.graph)
    if a.stats:
        stats(g)
    elif a.note:
        traverse(g, a.note, a.hops)
    elif a.entity:
        search(g, a.entity, a.limit)
    elif a.question:
        search(g, a.question, a.limit)
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
