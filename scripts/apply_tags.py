#!/usr/bin/env python3
# Apply a tags message to the MOST-RECENTLY-saved Beauty Library card.
# First tag = category (hijab|hair|hairstyle|makeup|wig). Rest -> matching facets + tags.
import sys, re, os, json, glob
LIB = os.environ.get("BEAUTY_LIB", "C:/Users/YOU/ObsidianVault/Beauty Library")
VOCAB = os.environ.get("BEAUTY_VOCAB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vocab.json"))
CATMAP = {"hijab": "hijab", "hair": "hairstyle", "hairstyle": "hairstyle", "makeup": "makeup", "wig": "wig"}

def norm(t): return re.sub(r"[\s_]+", "-", t.strip().lower())

raw = " ".join(sys.argv[1:]).strip() or sys.stdin.read()
parts = re.split(r"[,\n]+", raw) if ("," in raw) else re.split(r"\s+", raw)
toks = [norm(t) for t in parts if t.strip()]
if not toks:
    print("no tags given"); sys.exit(0)
cards = sorted([p for p in glob.glob(os.path.join(LIB, "*.md")) if not os.path.basename(p).startswith("_")], key=os.path.getmtime, reverse=True)
if not cards:
    print("no cards to tag"); sys.exit(1)
card = cards[0]
vocab = json.load(open(os.path.expanduser(VOCAB), encoding="utf-8"))
facet_of = {}
for grp in ("closed", "open"):
    for fac, vals in vocab.get(grp, {}).items():
        for v in vals: facet_of[v] = fac

cat = None
if toks and toks[0] in CATMAP:
    cat = CATMAP[toks[0]]; toks = toks[1:]

s = open(card, encoding="utf-8").read()
pre, fm, body = s.split("---", 2)
rows = []
for ln in fm.strip("\n").split("\n"):
    m = re.match(r'^([A-Za-z_-]+):\s*(.*)$', ln)
    if not m: rows.append(("_raw", "raw", ln)); continue
    k, v = m.group(1), m.group(2)
    if v.startswith("[") and v.endswith("]"):
        items = [x.strip().strip('"') for x in v[1:-1].split(",") if x.strip()]
        rows.append((k, "list", items))
    else:
        rows.append((k, "scalar", v))

def get(k): return next((r for r in rows if r[0] == k), None)
def setscalar(k, val):
    r = get(k)
    if r: rows[rows.index(r)] = (k, "scalar", val)
    else: rows.append((k, "scalar", val))
def addlist(k, vals):
    r = get(k)
    if r:
        cur = r[2] if isinstance(r[2], list) else ([r[2]] if r[2] else [])
        cur = cur + [v for v in vals if v not in cur]
        rows[rows.index(r)] = (k, "list", cur)
    else:
        rows.append((k, "list", list(vals)))

if cat:
    setscalar("category", cat); setscalar("type", cat)
free = []
for t in toks:
    f = facet_of.get(t)
    if f: addlist(f, [t])
    else: free.append(t)
allvals = []
for k, kind, v in rows:
    if kind == "list" and k != "tags": allvals += v
allvals += free
seen = set(); flat = []
for t in allvals:
    if t and t not in seen: seen.add(t); flat.append(t)
addlist("tags", [])
r = get("tags"); rows[rows.index(r)] = ("tags", "list", flat)

out = []
for k, kind, v in rows:
    if kind == "raw": out.append(v)
    elif kind == "list": out.append(k + ": [" + ", ".join(json.dumps(x) for x in v) + "]")
    else: out.append(k + ": " + v)
open(card, "w", encoding="utf-8").write(pre + "---\n" + "\n".join(out) + "\n---" + body)
print("tagged:", os.path.basename(card), "| category=", cat or "(unchanged)", "| +tags:", toks)

# auto-refresh the searchable gallery after tagging
try:
    import subprocess as _sp, sys as _sys, os as _os
    _sp.run([_sys.executable, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build_gallery.py")], timeout=120)
except Exception:
    pass
