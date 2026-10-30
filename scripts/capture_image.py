#!/usr/bin/env python3
# Create a Beauty Library card from a SENT IMAGE (and optional source link, e.g. Etsy).
# Usage: capture_image.py --image <path> [--source <url>] [--title <t>] [--context <t>] [--category hairstyle]
import os, re, json, shutil, datetime, argparse, subprocess
LIB    = "C:/Users/YOU/ObsidianVault/Beauty Library"
VAULT  = "C:/Users/YOU/ObsidianVault"
THUMBS = os.path.join(VAULT, "_BeautyLibrarian", "thumbs"); os.makedirs(THUMBS, exist_ok=True)

ap = argparse.ArgumentParser()
ap.add_argument("--image", required=True)
ap.add_argument("--source", default="")
ap.add_argument("--title", default="")
ap.add_argument("--context", default="")
ap.add_argument("--category", default="hairstyle")
a = ap.parse_args()

if not os.path.exists(a.image):
    raise SystemExit("image not found: " + a.image)

def slug(t): return (re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:60]) or "look"
title = a.title.strip() or ("Saved hair look " + datetime.datetime.now().strftime("%b %d %H%M"))
sl = slug(title); base = sl; n = 2
while os.path.exists(os.path.join(LIB, sl + ".md")):
    sl = f"{base}-{n}"; n += 1

ext = os.path.splitext(a.image)[1].lower()
if ext not in (".jpg", ".jpeg", ".png", ".webp"): ext = ".jpg"
shutil.copyfile(a.image, os.path.join(THUMBS, sl + ext))
thumb = "_BeautyLibrarian/thumbs/" + sl + ext

created = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S (UTC -04:00)")
ctx = a.context.strip() or ("Saved image reference" + (" — purchased hair" if a.source else ""))
fm = ["---", f"title: {json.dumps(title)}", f"category: {a.category}", "source_type: image"]
if a.source: fm.append(f"source_url: {a.source}")
fm.append(f"thumbnail: {thumb}")
fm.append(f"context: {json.dumps(ctx)}")
for k, v in (("body-part", ["hair"]), ("accessibility", ["none"]),
             ("suitable-for", ["none"]), ("accessory", ["none"]), ("tool", ["none"])):
    fm.append(f"{k}: [" + ", ".join(json.dumps(x) for x in v) + "]")
fm += ['tags: ["hair"]', f"created: {created}", f"type: {a.category}", "---"]
body = [f"\n# {title}\n", f"![saved look]({thumb})\n"]
if ctx: body.append(f"**Context:** {ctx}  ")
if a.source: body.append(f"**Source:** {a.source}  ")
body.append("\n## My Notes\n")
open(os.path.join(LIB, sl + ".md"), "w", encoding="utf-8").write("\n".join(fm) + "\n" + "\n".join(body) + "\n")
print("created card:", sl + ".md", "| image saved to thumbs/" + sl + ext)

try:
    subprocess.run(["python", os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_gallery.py")], timeout=120)
except Exception:
    pass
