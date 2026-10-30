#!/usr/bin/env python3
"""
save_to_capacities.py — Capacities API helpers + YouTube deep-link/thumbnail utilities.

Used by capture.py; also runnable standalone (`python save_to_capacities.py`) to self-test the
pure helper functions without touching the network.

Capacities API:
  - Auth: Bearer token via CAPACITIES_API_KEY
  - Space: CAPACITIES_SPACE_ID (space UUID)
  - Base: https://api.capacities.io
  - Endpoints used: POST /save-weblink (url, titleOverride, tags, mdText, spaceId)
                    POST /save-to-daily-note (mdText, spaceId)
  - Rate limit ~10 saves / 60s.
The API cannot create custom "Look" objects directly; for proper typed objects with full metadata,
bulk-import the markdown folder via Settings -> Import Content and map frontmatter to properties.
"""

import json
import os
import re
import sys
import urllib.request

BASE_URL = "https://api.capacities.io"


def ts_to_seconds(ts):
    """'0:42' -> 42, '1:01:05' -> 3665, '90' -> 90."""
    parts = [int(p) for p in str(ts).strip().split(":")]
    seconds = 0
    for p in parts:
        seconds = seconds * 60 + p
    return seconds


def video_id(url):
    """Extract an 11-char YouTube id from common URL shapes, else None."""
    m = re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else None


def deep_link(url, seconds):
    """Tap-to-jump YouTube deep-link; falls back to ?t= on the original url."""
    vid = video_id(url)
    if vid:
        return f"https://youtu.be/{vid}?t={int(seconds)}"
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}t={int(seconds)}"


def thumbnail_for(url):
    """Best-effort final-look image without downloading the video."""
    vid = video_id(url)
    if vid:
        return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    return None


def api_post(path, body):
    api_key = os.environ.get("CAPACITIES_API_KEY")
    if not api_key:
        raise RuntimeError("CAPACITIES_API_KEY not set")
    req = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8", "replace")
        return json.loads(raw) if raw.strip() else {}


def _selftest():
    assert ts_to_seconds("0:42") == 42
    assert ts_to_seconds("1:01:05") == 3665
    assert ts_to_seconds("90") == 90
    assert video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert video_id("https://youtube.com/shorts/abcdefghijk") == "abcdefghijk"
    assert deep_link("https://www.youtube.com/watch?v=dQw4w9WgXcQ", 190) == \
        "https://youtu.be/dQw4w9WgXcQ?t=190"
    assert thumbnail_for("https://youtu.be/dQw4w9WgXcQ") == \
        "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
    print("self-test: OK", file=sys.stderr)


if __name__ == "__main__":
    _selftest()
