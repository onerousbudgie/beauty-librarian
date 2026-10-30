#!/usr/bin/env python3
# Append a freeform NOTE to the MOST-RECENTLY-saved Beauty Library card.
# Used by the bot when a DM is a comment/remark (not a link, not a tag list).
import sys, os, glob, datetime
LIB = os.environ.get("BEAUTY_LIB", "C:/Users/YOU/ObsidianVault/Beauty Library")

note = " ".join(sys.argv[1:]).strip()
if not note:
    note = sys.stdin.read().strip()
if not note:
    print("no note given"); sys.exit(0)

cards = sorted([f for f in glob.glob(os.path.join(LIB, "*.md")) if not os.path.basename(f).startswith("_")], key=os.path.getmtime, reverse=True)
if not cards:
    print("no cards to note"); sys.exit(1)
card = cards[0]

stamp = datetime.datetime.now().strftime("%Y-%m-%d")
bullet = f"- {note}  _({stamp})_"

s = open(card, encoding="utf-8").read()
if "## My Notes" in s:
    s = s.rstrip() + "\n" + bullet + "\n"
else:
    s = s.rstrip() + "\n\n## My Notes\n\n" + bullet + "\n"
open(card, "w", encoding="utf-8").write(s)
print("note added to", os.path.basename(card))
