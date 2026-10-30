#!/usr/bin/env python3
"""
tag_review.py — monthly tag hygiene for the beauty-library.

Scans every markdown entry's frontmatter, collects the tags actually in use, and reports:
  1. NEW open-facet tags not yet in vocab.json (from proposed_tags.log + live scan)
  2. SUSPECTED near-duplicates (e.g. 'flexi-rods' vs 'flexirod', 'smoky-eye' vs 'smokey-eye')

It does NOT merge anything. Output is a short report you approve from — wire the printed report to
your Telegram channel via your OpenClaw messaging skill, then tap to confirm any merge by hand.

Usage:
  python tag_review.py --library ~/beauty-library --vocab ../vocab.json

Run monthly via the OpenClaw heartbeat.
"""

import argparse
import json
import os
import re
import sys
from difflib import SequenceMatcher


def load_vocab(path):
    with open(os.path.expanduser(path), encoding="utf-8") as f:
        return json.load(f)


def known_values(vocab):
    vals = set()
    for group in ("closed", "open"):
        for _facet, lst in vocab.get(group, {}).items():
            vals.update(lst)
    return vals


def open_facets(vocab):
    return set(vocab.get("open", {}).keys())


FACET_LINE = re.compile(r"^([a-z-]+):\s*\[(.*)\]\s*$")


def scan_library(lib):
    """Return {facet: set(values)} found across all entries' frontmatter."""
    found = {}
    for name in os.listdir(lib):
        if not name.endswith(".md"):
            continue
        path = os.path.join(lib, name)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if not text.startswith("---"):
            continue
        fm = text.split("---", 2)[1]
        for line in fm.splitlines():
            m = FACET_LINE.match(line.strip())
            if not m:
                continue
            facet, body = m.group(1), m.group(2)
            vals = [v.strip().strip('"') for v in body.split(",") if v.strip()]
            found.setdefault(facet, set()).update(vals)
    return found


def near_dupes(values, threshold=0.85):
    vals = sorted(values)
    pairs = []
    for i in range(len(vals)):
        for j in range(i + 1, len(vals)):
            a, b = vals[i], vals[j]
            if a == b:
                continue
            ratio = SequenceMatcher(None, a, b).ratio()
            # also catch substring / de-hyphenated forms
            squashed = a.replace("-", "") == b.replace("-", "")
            if ratio >= threshold or squashed:
                pairs.append((a, b, round(ratio, 2)))
    return pairs


def read_proposed_log(lib):
    path = os.path.join(lib, "proposed_tags.log")
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3:
                rows.append({"when": parts[0], "facet": parts[1], "value": parts[2]})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--library", required=True)
    ap.add_argument("--vocab", default=os.path.join(os.path.dirname(__file__), "..", "vocab.json"))
    args = ap.parse_args()

    lib = os.path.expanduser(args.library)
    vocab = load_vocab(args.vocab)
    known = known_values(vocab)
    open_set = open_facets(vocab)

    found = scan_library(lib)

    # 1) new open-facet tags in use but not yet in vocab
    new_in_use = []
    for facet, vals in found.items():
        if facet not in open_set:
            continue
        for v in sorted(vals):
            if v not in known:
                new_in_use.append((facet, v))

    proposed = read_proposed_log(lib)

    # 2) suspected dupes, per facet, across vocab + live values
    dupe_report = {}
    for facet in open_set:
        pool = set(vocab.get("open", {}).get(facet, [])) | found.get(facet, set())
        d = near_dupes(pool)
        if d:
            dupe_report[facet] = d

    # ---- report ----
    lines = ["BEAUTY-LIBRARIAN — MONTHLY TAG REVIEW", "=" * 38, ""]
    if new_in_use:
        lines.append("NEW open-facet tags in use (add to vocab.json to bless them):")
        for facet, v in new_in_use:
            lines.append(f"  - {facet}: {v}")
        lines.append("")
    if proposed:
        lines.append(f"Proposed-tag log entries this period: {len(proposed)}")
        for r in proposed[-20:]:
            lines.append(f"  - {r['facet']}: {r['value']}  ({r['when'][:10]})")
        lines.append("")
    if dupe_report:
        lines.append("SUSPECTED near-duplicates (confirm a merge by hand):")
        for facet, pairs in dupe_report.items():
            for a, b, ratio in pairs:
                lines.append(f"  - {facet}: '{a}' <-> '{b}'  (sim {ratio})")
        lines.append("")
    if not (new_in_use or proposed or dupe_report):
        lines.append("All clean — no new tags or suspected duplicates. ")

    report = "\n".join(lines)
    print(report)
    # OpenClaw: pipe `report` to your Telegram messaging skill here.
    return report


if __name__ == "__main__":
    main()
