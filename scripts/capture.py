#!/usr/bin/env python3
"""
capture.py — normalize beauty/style entries from ANY source into one faceted library.

Reads JSON on stdin:
{
  "library_dir": "~/beauty-library",   # where .md files are written (required)
  "vocab_path": "../vocab.json",        # optional; defaults to vocab.json next to the skill
  "push_to_capacities": false,          # also send live via the Capacities API
  "entries": [ <entry>, ... ]           # one or more; schema in SKILL.md
}

For each entry:
  - validates CLOSED facets against vocab.json (drops + warns on unknown values)
  - allows OPEN facets to introduce new normalized values, logging them to proposed_tags.log
  - writes one markdown file (slugified title) with all facets in YAML frontmatter
  - leads with a thumbnail (auto-derived for YouTube if not supplied)
  - optionally pushes to Capacities

Requires save_to_capacities.py in the same folder. For API push: CAPACITIES_API_KEY,
CAPACITIES_SPACE_ID in the environment.
"""

import json
import os
import re
import sys
import urllib.error
from datetime import datetime

import tag_helpers as cap


def warn(msg):
    print(f"[beauty-librarian] {msg}", file=sys.stderr)


def slugify(title):
    s = re.sub(r"[^\w\s-]", "", title.strip().lower())
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-") or "untitled"


def normalize_tag(v):
    return re.sub(r"[\s_]+", "-", str(v).strip().lower())


def is_video(entry):
    return entry.get("source_type") in ("youtube", "youtube_short")


def now_stamp():
    """Obsidian-vault convention: 2026-06-06T14:09:37 (UTC -04:00)."""
    local = datetime.now().astimezone()
    off = local.utcoffset()
    total = int(off.total_seconds() // 60)
    sign = "+" if total >= 0 else "-"
    hh, mm = divmod(abs(total), 60)
    return local.strftime("%Y-%m-%dT%H:%M:%S") + f" (UTC {sign}{hh:02d}:{mm:02d})"


def load_vocab(payload):
    path = payload.get("vocab_path")
    if not path:
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "..", "vocab.json")
    with open(os.path.expanduser(path), encoding="utf-8") as f:
        return json.load(f)


def validate_facets(entry, vocab, lib):
    """Enforce closed facets; allow + log open-facet proposals. Returns cleaned facet dict."""
    closed = vocab.get("closed", {})
    open_f = vocab.get("open", {})
    facets_in = entry.get("facets", {}) or {}
    out = {}

    for facet, values in facets_in.items():
        vals = [normalize_tag(v) for v in (values or [])]
        if facet in closed:
            allowed = set(closed[facet])
            kept, dropped = [], []
            for v in vals:
                (kept if v in allowed else dropped).append(v)
            for v in dropped:
                warn(f"'{entry.get('title','?')}': dropped unknown {facet} value '{v}' "
                     f"(closed facet — add it to vocab.json if intended)")
            out[facet] = kept
        elif facet in open_f:
            known = set(open_f[facet])
            new = [v for v in vals if v not in known]
            for v in new:
                log_proposed(lib, facet, v, entry.get("title", "?"))
            out[facet] = vals
        else:
            warn(f"'{entry.get('title','?')}': unknown facet '{facet}' ignored")
    return out


def log_proposed(lib, facet, value, title):
    path = os.path.join(lib, "proposed_tags.log")
    line = f"{datetime.now().isoformat(timespec='seconds')}\t{facet}\t{value}\t{title}\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
    warn(f"proposed new {facet} tag '{value}' (logged for monthly review)")


def all_tags(facets):
    """Flatten every facet value into one tag list (for Capacities tags / search)."""
    tags = []
    for vals in facets.values():
        tags.extend(vals)
    # de-dupe, preserve order
    seen, out = set(), []
    for t in tags:
        if t and t not in seen:
            seen.add(t); out.append(t)
    return out


def combined_tags(entry, facets):
    """Facet-derived tags PLUS any free-form user tags from the post (no vocab needed)."""
    base = all_tags(facets)
    extra = [normalize_tag(t) for t in (entry.get("extra_tags") or [])]
    seen, out = set(), []
    for t in base + extra:
        if t and t not in seen:
            seen.add(t); out.append(t)
    return out


def steps_markdown(entry):
    lines = []
    for step in entry.get("steps", []):
        label = step.get("label", "").strip()
        note = step.get("note", "").strip()
        t = step.get("t")
        if is_video(entry) and t and entry.get("source_url"):
            link = cap.deep_link(entry["source_url"], cap.ts_to_seconds(t))
            head = f"- [{t}]({link}) {label}"
        elif t:
            head = f"- ({t}) {label}"
        else:
            head = f"- {label}"
        if note:
            head += f" — _{note}_"
        lines.append(head)
    return "\n".join(lines)


def _localize_thumb(thumb, entry):
    """Blog/web lead images are often hotlink-protected and won't render.
    Download them once into the vault so the card always shows a picture.
    Leave Pinterest/YouTube CDNs as remote URLs (they render fine)."""
    try:
        if not thumb or not str(thumb).startswith("http"):
            return thumb
        import urllib.parse as _up
        host = _up.urlparse(thumb).netloc.lower()
        if any(h in host for h in ("pinimg.com", "ytimg.com", "youtube.com", "ggpht.com")):
            return thumb
        import os as _os, re as _re, urllib.request as _ur
        vault = "C:/Users/YOU/ObsidianVault"
        tdir = _os.path.join(vault, "_BeautyLibrarian", "thumbs")
        _os.makedirs(tdir, exist_ok=True)
        slug = _re.sub(r"[^a-z0-9]+", "-", (entry.get("title") or "look").lower()).strip("-")[:60] or "look"
        ext = ".jpg"
        for e in (".jpg", ".jpeg", ".png", ".webp"):
            if thumb.lower().split("?")[0].endswith(e):
                ext = e; break
        dst = _os.path.join(tdir, slug + ext)
        req = _ur.Request(thumb, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Referer": entry.get("source_url") or thumb,
            "Accept": "image/avif,image/webp,image/*,*/*"})
        data = _ur.urlopen(req, timeout=25).read()
        if data and len(data) > 1500:
            open(dst, "wb").write(data)
            return "_BeautyLibrarian/thumbs/" + slug + ext
        return thumb
    except Exception:
        return thumb


def to_markdown(entry, facets):
    category = entry.get("category", "hairstyle")
    thumb = entry.get("thumbnail") or (cap.thumbnail_for(entry.get("source_url")) if entry.get("source_url") else None)
    thumb = _localize_thumb(thumb, entry)

    fm = ["---"]
    fm.append(f'title: {json.dumps(entry["title"])}')
    fm.append(f"category: {category}")
    if entry.get("source_type"):
        fm.append(f'source_type: {entry["source_type"]}')
    if entry.get("source_url"):
        fm.append(f'source_url: {entry["source_url"]}')
    if entry.get("segment"):
        fm.append(f'segment: {json.dumps(entry["segment"])}')
    if thumb:
        fm.append(f"thumbnail: {thumb}")
    if entry.get("context"):
        fm.append(f'context: {json.dumps(entry["context"])}')
    for facet, vals in facets.items():
        if vals:
            fm.append(f"{facet}: [" + ", ".join(json.dumps(v) for v in vals) + "]")
    fm.append(f"tags: [" + ", ".join(json.dumps(t) for t in combined_tags(entry, facets)) + "]")
    fm.append(f"created: {now_stamp()}")
    fm.append(f"type: {category}")
    fm.append("---")

    body = [f"\n# {entry['title']}\n"]
    if thumb:
        body.append(f"![final look]({thumb})\n")
    if entry.get("context"):
        body.append(f"**Context:** {entry['context']}  ")
    if entry.get("source_url"):
        body.append(f"**Source:** {entry['source_url']}  ")
    body.append("\n## Steps\n")
    body.append(steps_markdown(entry) or "_no steps captured_")
    body.append("")
    return "\n".join(fm) + "\n" + "\n".join(body)


def push(entry, facets, space_id):
    md_steps = steps_markdown(entry)
    tags = combined_tags(entry, facets)
    if entry.get("source_url"):
        url = entry["source_url"]
        seg = entry.get("segment") or {}
        if is_video(entry) and seg.get("start"):
            url = cap.deep_link(entry["source_url"], cap.ts_to_seconds(seg["start"]))
        body = {"spaceId": space_id, "url": url, "titleOverride": entry["title"],
                "tags": tags, "mdText": md_steps}
        return cap.api_post("/save-weblink", body)
    category = entry.get("category", "hairstyle")
    tagline = " ".join(f"#{t}" for t in tags)
    md = f"## {entry['title']}  #{category} {tagline}\n\n{md_steps}"
    return cap.api_post("/save-to-daily-note", {"spaceId": space_id, "mdText": md})


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        warn("no JSON on stdin"); sys.exit(1)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        warn(f"bad JSON: {e}"); sys.exit(1)

    entries = payload.get("entries") or []
    if not entries:
        warn("no entries to capture"); sys.exit(1)

    vocab = load_vocab(payload)
    lib = os.path.expanduser(payload.get("library_dir", "~/beauty-library"))
    os.makedirs(lib, exist_ok=True)

    do_push = bool(payload.get("push_to_capacities"))
    space_id = os.environ.get("CAPACITIES_SPACE_ID")
    if do_push and not space_id:
        warn("push_to_capacities set but CAPACITIES_SPACE_ID missing — writing files only")
        do_push = False

    required = vocab.get("always_required", [])
    written, pushed = [], 0
    for entry in entries:
        if not entry.get("title"):
            warn("skipping an entry with no title"); continue
        facets = validate_facets(entry, vocab, lib)
        # suitable-for default: makeup -> not-applicable, others -> none
        if not facets.get("suitable-for"):
            facets["suitable-for"] = ["not-applicable"] if entry.get("category") == "makeup" else ["none"]
        # accessibility default: none when unset
        if not facets.get("accessibility"):
            facets["accessibility"] = ["none"]
        for req in required:
            if req == "category":
                if not entry.get("category"):
                    warn(f"'{entry['title']}': missing required 'category'")
            elif not facets.get(req):
                warn(f"'{entry['title']}': missing required facet '{req}'")
        path = os.path.join(lib, slugify(entry["title"]) + ".md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(to_markdown(entry, facets))
        written.append(path)
        if do_push:
            try:
                push(entry, facets, space_id); pushed += 1
            except urllib.error.HTTPError as e:
                warn(f"Capacities HTTP {e.code} for '{entry['title']}': "
                     f"{e.read().decode('utf-8','replace')[:200]}")
            except Exception as e:  # noqa: BLE001
                warn(f"push failed for '{entry['title']}': {e}")

    print(f"wrote {len(written)} file(s) to {lib}")
    for p in written:
        print(f"  - {p}")
    if do_push:
        print(f"pushed {pushed}/{len(written)} to Capacities")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    # auto-refresh the searchable gallery after writing
    try:
        import subprocess as _sp, sys as _sys, os as _os
        _sp.run([_sys.executable, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build_gallery.py")], timeout=120)
    except Exception:
        pass
