#!/usr/bin/env python3
"""
context-graph — scan a folder of markdown notes and build the structural skeleton
of a knowledge graph.

This script does the deterministic half: files, wikilinks, tags, headings, and
which notes mention which other notes. It does NOT try to infer entity types or
relationships from prose — that is the model's job, and it is done by the skill
in a second pass (see SKILL.md).

Output is a single JSON file. Re-running only re-reads files whose contents have
changed, so updates are cheap.

Usage:
    python3 build_graph.py <notes_dir> [--out graph.json] [--rebuild]
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
MDLINK = re.compile(r"\[[^\]]*\]\(([^)]+\.md)\)")
TAG = re.compile(r"(?:^|\s)#([A-Za-z][\w/-]{1,60})")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.M)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()[:16]


def note_id(path: str, root: str) -> str:
    return os.path.relpath(path, root).replace(os.sep, "/")


def title_of(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def parse_note(path: str, root: str) -> dict:
    with open(path, encoding="utf-8", errors="ignore") as fh:
        raw = fh.read()

    body = raw
    front = {}
    m = FRONTMATTER.match(raw)
    if m:
        body = raw[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                k, _, v = line.partition(":")
                front[k.strip()] = v.strip()

    links = [t.strip() for t in WIKILINK.findall(body)]
    links += [os.path.splitext(os.path.basename(t))[0] for t in MDLINK.findall(body)]

    return {
        "id": note_id(path, root),
        "title": title_of(path),
        "path": os.path.relpath(path, root),
        "frontmatter": front,
        "tags": sorted(set(TAG.findall(body))),
        "headings": [h[1].strip() for h in HEADING.findall(body)][:40],
        "links": sorted(set(links)),
        "words": len(body.split()),
        "hash": sha(body),
        # filled in by the model pass — see SKILL.md
        "entities": [],
        "relations": [],
        "extracted": False,
    }


def walk(root: str, skip: set) -> list:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        for fn in filenames:
            if fn.lower().endswith(".md"):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the structural layer of a notes knowledge graph.")
    ap.add_argument("notes_dir")
    ap.add_argument("--out", default="graph.json")
    ap.add_argument("--rebuild", action="store_true", help="discard existing extractions and start clean")
    args = ap.parse_args()

    root = os.path.abspath(os.path.expanduser(args.notes_dir))
    if not os.path.isdir(root):
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 1

    previous = {}
    if os.path.exists(args.out) and not args.rebuild:
        try:
            with open(args.out, encoding="utf-8") as fh:
                for n in json.load(fh).get("notes", []):
                    previous[n["id"]] = n
        except Exception:
            pass

    skip = {"node_modules", "__pycache__", ".obsidian", ".git", ".trash"}
    paths = walk(root, skip)

    notes, unchanged, updated = [], 0, 0
    for p in paths:
        n = parse_note(p, root)
        old = previous.get(n["id"])
        if old and old.get("hash") == n["hash"]:
            # content identical — keep whatever the model already extracted
            n["entities"] = old.get("entities", [])
            n["relations"] = old.get("relations", [])
            n["extracted"] = old.get("extracted", False)
            unchanged += 1
        else:
            updated += 1
        notes.append(n)

    # Backlinks, resolved case-insensitively against note titles.
    by_title = {}
    for n in notes:
        by_title.setdefault(n["title"].lower(), n["id"])
    for n in notes:
        n["links_resolved"] = sorted({by_title[l.lower()] for l in n["links"] if l.lower() in by_title})
    backlinks = {n["id"]: [] for n in notes}
    for n in notes:
        for target in n["links_resolved"]:
            backlinks[target].append(n["id"])
    for n in notes:
        n["backlinks"] = sorted(set(backlinks[n["id"]]))

    graph = {
        "version": 1,
        "root": root,
        "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "notes": notes,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(graph, fh, indent=1, ensure_ascii=False)

    pending = sum(1 for n in notes if not n["extracted"])
    edges = sum(len(n["links_resolved"]) for n in notes)
    print(f"notes: {len(notes)}  (unchanged {unchanged}, new/changed {updated})")
    print(f"wikilink edges resolved: {edges}")
    print(f"awaiting model extraction: {pending}")
    print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
