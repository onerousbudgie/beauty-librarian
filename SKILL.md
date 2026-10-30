---
name: beauty-librarian
description: Capture a hair / makeup / hijab style reference — pasted text, a web/blog tutorial, a YouTube video, or a Short — into the user's Obsidian "Beauty Library" as a tagged markdown card with a thumbnail. Splits one video that demos several looks into one entry per look, each deep-linked to its timestamp. TRIGGER when a message arrives at the Workflow Director bot (@YourOpenClawBot) that is a beauty/style tutorial link or text, OR is tagged #beauty, OR when asked to "add this look", "save this to my beauty library", "clip the useful parts", or "split these into separate styles". ALSO TRIGGER on ANY message posted in the user's "Beauty Library Channel" (Telegram chat id <YOUR_TELEGRAM_CHANNEL_ID>, on the director account @YourOpenClawBot): treat every post there as a capture and run this skill on it.
---

# beauty-librarian

Turns a tutorial (text, web page, YouTube, Short) into clean, tagged entries in the user's Obsidian
**Beauty Library**, spanning **hairstyle**, **makeup**, and **hijab**. Every source normalizes to the
same faceted schema and is written as one markdown file per look, leading with the final-look thumbnail.

## RUN CONFIG — the user's setup (read this first)

- **library_dir:** `C:/Users/YOU/ObsidianVault/Beauty Library`
- **push_to_capacities:** always `false` (Capacities is not used — Obsidian is the home).
- **Process immediately** on receipt (this is low-volume; do NOT queue-and-sweep like the PKM skills).
  Write the entry, then reply with ONE line: `✅ Saved: <title>` (or, for a multi-look split,
  `✅ Saved N looks: <titles>`).
- **yt-dlp:** installed at `C:/Users/YOU/AppData/Roaming/Python/Python313/Scripts/yt-dlp.exe` (already on PATH). Use it for transcript,
  chapters, and thumbnail. `ffmpeg` is NOT installed — only needed for optional video *clipping*,
  which this skill does not require.
- **YouTube cookies:** try WITHOUT cookies first (home IP usually works). If a video is blocked or
  age-restricted, ask the user to export `cookies.txt` and pass `--cookies <path>` to yt-dlp.
- **Trigger:** messages to the Workflow Director bot (@YourOpenClawBot). A bare link = process the
  whole thing. An instruction after the link (e.g. "style 2 only", "2:45-3:30", "just the bun")
  selects a sub-part. `#beauty` is an explicit opt-in if auto-detection is unsure.

## One entry per look

Give each style its own entry, title, thumbnail, and steps. If a video demos several looks, produce
several entries (see "Splitting").

## The faceted schema

Every entry is tagged across FACETS. Read `vocab.json` at run time — it is the source of truth.

- **CLOSED facets** — pick ONLY from the list in `vocab.json`. Never invent a value.
- **OPEN facets** — pick from the list when something fits; if nothing fits you MAY propose a new
  value, but (a) normalize it lowercase-hyphenated, (b) check it isn't a near-duplicate, and
  (c) it gets logged to `proposed_tags.log` for the monthly review. Never silently rename/merge.

### Closed facets
- `category`: hairstyle | makeup | hijab | wig
- `body-part`: eyes, lips, face, brows, lashes, nails, hair, head
- `silhouette` (hair): updo, half-up, down, bun, ponytail, braids, wash-n-go
- `effort`: quick, medium, involved
- `occasion`: everyday, work, gym, event, formal, date, travel, lounging, errands, religious, photoshoot, sleep
- `vibe`: soft, glam, edgy, natural, elegant, playful, dramatic, romantic, sleek, messy, bold, minimal, vintage, trendy
- `state`: wash-day, freshly-washed, second-day-hair, third-day-hair, refresh, dry-hair, wet-hair, damp-hair, overnight, gym-ready, grown-out, bare-face
- `accessibility`: one-handed, chronic-pain, neurodivergence, low-manipulation, none
- `suitable-for`: hat-friendly, helmet-friendly, hood-friendly, sleep-friendly, workout-friendly, none, not-applicable
  (what a style can TOLERATE worn UNDER a hat/helmet. For hairstyle/hijab, assess it. For makeup, default `not-applicable`.)

### Open facets (propose-normalize-flag)
- `accessory`: none, scarf, headband, hat, claw-clip, clip-in, wig-piece, false-lashes, jewelry, hair-pins, hair-comb, french-comb, half-up-comb, wig-headband, bun-maker
- `tool`: none, no-heat, no-tools, diffuser, blow-dryer, flat-iron, curling-wand, hot-air-brush, flexi-rods, rollers, beauty-blender, lash-curler
- `technique`: wash-n-go, twist-out, braid-out, bantu-knots, flat-twist, halo-braid, space-buns, smoky-eye, cut-crease, winged-liner, false-lashes, soft-glam, no-makeup, contour, blush, highlight

### Always present
Every entry must set: `category`, `body-part`, `effort`, `accessory` (`none` if none), `tool`
(`none`/`no-heat`/`no-tools`). `silhouette` required for hairstyle. `accessibility` and `suitable-for`
default to `none` when nothing applies (makeup `suitable-for` defaults to `not-applicable`).

## The entry JSON (assemble per look, then pass to capture.py)

```json
{
  "title": "Hat-friendly low bun, soft vibe",
  "category": "hairstyle",
  "source_type": "text | web | youtube | youtube_short",
  "source_url": "https://...",
  "segment": {"start": "0:42", "end": "4:10"},
  "thumbnail": "https://i.ytimg.com/vi/ID/hqdefault.jpg",
  "context": "high-density 3c/4a",
  "facets": { "body-part": ["hair"], "silhouette": ["bun","updo"], "effort": ["quick"],
              "occasion": ["work"], "vibe": ["soft"], "state": ["second-day-hair"],
              "accessibility": ["low-manipulation"], "suitable-for": ["hat-friendly"],
              "accessory": ["none"], "tool": ["no-heat"], "technique": [] },
  "steps": [ {"t": "0:42", "label": "Gather low at nape", "note": "no tension on edges"} ]
}
```

`t` on steps only for video sources.

## Routing by source type

- **Pasted text** — structure straight into the schema, no fetch. Multiple styles → one entry each.
- **Web/blog page** — fetch + read the article, pull steps and any product list. Listicle (each H2 a
  look) → one entry per look. Summarize long articles to the technique steps. Lead image → thumbnail.
- **YouTube (long)** — get the timestamped transcript with yt-dlp, then split + select (below).
- **YouTube Short** — same, usually one segment.

### Getting a YouTube transcript with yt-dlp (no third-party skill needed)
```bash
export PATH=$HOME/.npm-global/bin:$PATH
# chapters + metadata:
yt-dlp --skip-download -J "<URL>" > /tmp/meta.json
# auto/ös subtitle as timestamped VTT:
yt-dlp --skip-download --write-auto-subs --write-subs --sub-langs "en.*" --sub-format vtt \
       -o "/tmp/yt/%(id)s" "<URL>"
```
Read the `.vtt` for timestamped lines; read `chapters` from the JSON for split boundaries. If a
video is blocked, add `--cookies <cookies.txt>`.

## Splitting one video into several looks
1. Prefer YouTube **chapters** (`chapters` in the `-J` JSON) for boundaries.
2. Fall back to transcript cues ("next look", "style two", "for this one").
3. Per look: set `segment.start/end`, keep only technique steps, deep-link every step `t` into the
   `source_url`. Drop intro/sponsor/outro.

## Thumbnail (final-look image)
YouTube/Shorts: use `https://i.ytimg.com/vi/<ID>/hqdefault.jpg` (capture.py derives this
automatically if you omit `thumbnail`). Web: the article's lead image.

## Output / capture
Pass assembled entries to `scripts/capture.py` as JSON on stdin, with the fixed library_dir:
```bash
cd C:/Users/YOU/.openclaw/workspace/skills/beauty-librarian/scripts
echo '{ "library_dir":"C:/Users/YOU/ObsidianVault/Beauty Library",
        "vocab_path":"../vocab.json", "push_to_capacities": false,
        "entries":[ <entry>, ... ] }' | python capture.py
```
It writes one markdown file per entry (slugified title) with facets in YAML frontmatter and a
`thumbnail`, and validates closed facets against vocab.json. The card then appears automatically on
the **Beauty Lookbook** base in Obsidian.

## Monthly tag review
`scripts/tag_review.py --library "C:/Users/YOU/ObsidianVault/Beauty Library"
--vocab ../vocab.json` — scans for new open-facet tags and near-duplicates, reports only. Never merges.

## Requirements
- `python` (have 3.14), `yt-dlp` (have, at C:/Users/YOU/AppData/Roaming/Python/Python313/Scripts). `ffmpeg` optional (clip mode only).
- Run locally (home IP) so YouTube doesn't block; add `--cookies` only if a specific video is blocked.

## Inbox enrichment mode (laptop browser button + phone share)
The browser button / phone share drops a stub note into the vault folder `_BeautyInbox/` (OUTSIDE the
Beauty Library, so raw stubs never clutter the lookbook). Each stub body looks like:
```
<source URL>
INSTRUCTION: <optional — may be absent = process the whole thing>
TITLE: <page title>
```
When OpenClaw is running, process the inbox:
1. List `C:/Users/YOU/ObsidianVault/_BeautyInbox/*.md` (ignore `.keep`).
2. For each stub: read the URL + optional instruction, run the normal beauty-librarian pipeline
   (route by source type, split multi-look videos, tag, thumbnail) and write the finished entr(y/ies)
   to the Beauty Library via capture.py (library_dir as in RUN CONFIG).
3. On success, DELETE the stub. On failure, leave it in place and report which one and why.
Trigger on the heartbeat (below) and on demand when the user says "enrich my beauty inbox".

## Channel capture (Beauty Library Channel)
the user posts hijab / wig / hair / makeup tutorial links into her Telegram **Beauty Library Channel**
(chat id `<YOUR_TELEGRAM_CHANNEL_ID>`, director account `@YourOpenClawBot`). Treat EVERY post in that channel
as a beauty capture:
1. Take the URL (and any instruction text in the same post) and run the normal pipeline
   (route by source type, fetch transcript/steps with yt-dlp where needed, split multi-look videos,
   tag from vocab.json, derive thumbnail).
2. Write the finished card(s) to the Beauty Library via scripts/capture.py
   (library_dir C:/Users/YOU/ObsidianVault/Beauty Library).
3. Reply in the channel with one line: `✅ Saved: <title>` (or `✅ Saved N looks: ...`).
A bare link = process the whole thing; an instruction in the post (e.g. "style 2 only", "just the bun")
selects a sub-part. This is the same skill as the laptop button — both end in the one Beauty Library.

## Tagging from the channel — the user's flow: link first, tags in a SEPARATE message
Share sheets usually won't let the user attach text to a shared link, so her normal flow is two messages:
  message 1 = just the link
  message 2 = the tags (a separate message, right after)
Handle it like her PKM "follow-up tags" pattern:
- When a channel post is essentially JUST a URL, and the NEXT message in that channel is short text with
  NO url, treat that second message as the TAGS for the link above it and MERGE them. Do NOT create a
  separate card from the tags message.
- "#" is OPTIONAL. Tags may be plain words, a comma list, or hashtags — all equivalent:
    "hijab wedding lace-front"  ==  "hijab, wedding, lace-front"  ==  "#hijab #wedding #lace-front"
- Apply EVERY tag: map any that match a vocab facet into that facet, and pass ALL of them in the entry's
  `extra_tags` so they always land in the card's `tags:` (normalized lowercase-hyphenated), vocab or not.
- A natural-language directive ("just the bun", "style 2 only", "2:45-3:30") is an INSTRUCTION (how to trim),
  not a tag.

Order of operations: if you already wrote the card from the link before the tags message arrives, just open
that most-recently-written card and add the new tags to its `tags:` (and matching facets) — keep it one card.
Tags may also be put in the SAME message as the link if the user's input allows it. the user never edits vocab.json.

## Tag exclusions
Never use the `no-heat` tag — the user does not want it. Omit it entirely.

## Pinterest pins (visual reference)
For `pinterest.com/...` or `pin.it/...` URLs (images, not tutorials): fetch the pin with a browser
User-Agent — `curl -sL -A "<browser UA>" "<url>"` — then extract `og:image` (use as the thumbnail),
`og:title` and `og:description` (title + tags). Classify category from keywords: scarf/headwrap/turban
-> hijab; wig/lace/frontal -> wig; makeup/eyeshadow/liner/lip/brow/lash/glam -> makeup; otherwise
hairstyle. Write ONE visual-reference card (source_type `web`, source_url the pin link, thumbnail =
og:image) with NO step-by-step (the image IS the look). Fill facets you can infer; default the rest.
Same idea for any plain web/blog page: use its lead image + title; pull steps if the article has them.

## Web/blog tutorials: SAVE A SNAPSHOT + pull the steps
For any web/blog tutorial URL, ALWAYS do BOTH:
1. Save a local HTML snapshot so it survives if the page dies:
   `curl -sL -A "<browser UA>" "<url>" > "C:/Users/YOU/ObsidianVault/_BeautyLibrarian/snapshots/<slug>.html"`
2. Extract the readable step-by-step from that HTML (the article body: headings, list items,
   paragraphs) and put it INTO the card under a `## Saved tutorial copy` heading, and reference the
   snapshot path `_BeautyLibrarian/snapshots/<slug>.html`. Use the article's `og:image` as the thumbnail.
So a blog card is self-contained: tags + thumbnail + the full steps offline + the saved HTML.

## Pinterest VIDEO pins
Some pins are videos, not stills. A pin is a VIDEO if the page has `og:video`, a `v.pinimg.com` URL, `"is_video":true`, or `[Video]` in the title. For a video pin: still use the cover frame (og:image) as the thumbnail, but ADD a `video` tag and a note in the card that it is a video to WATCH at the Source link (not a still image).

## AUTHORITATIVE CATEGORY — the user dictates it
If the user's tags (in the post or the follow-up tags message) include a main-category word —
`hijab`, `hair`/`hairstyle`, `makeup`, or `wig` — set the card's `category` to EXACTLY that and do
NOT override it with a keyword guess. She decides whether a scarf/headwrap look is hijab or hair;
her word always wins. Only guess the category when she hasn't stated one.

## RELIABLE TAGGING — apply tags in the SAME turn
Most reliable: when the link and tags arrive in the SAME message, ALWAYS apply both in that one
turn (set category from the FIRST tag, apply the rest). This is guaranteed. If tags arrive as a
separate FOLLOWING message, update the most-recently-written card with them (merge into tags +
matching facets) — supported, but same-message is the sure path. NEVER drop the user's tags.

## Notes, images & purchased hair (added 2026-06-24)
the user sends a LINK first, then follow-up DMs. Route each follow-up by content:
- **Tags** = a short comma/space list of descriptors (e.g. `hijab, everyday, soft`). First word may be the category.
  Run: `python scripts/apply_tags.py "<message>"`
- **Note** = a freeform sentence/remark about the look (e.g. "this could also work for a wedding").
  Run: `python scripts/add_note.py "<message>"`  → appended under a `## My Notes` heading on the most-recent card.
  A message starting with `note:` is ALWAYS a note (strip the prefix).
- Typical order: first follow-up = tags, a later sentence = note. Judge by content; a single follow-up can be either.

**Sent IMAGE / purchased hair (Etsy):** If a DM includes a PHOTO attachment, the gateway saves it and provides
its file path (mediaPath, e.g. `C:/Users/YOU/.openclaw/media/inbound/<id>.jpg`). Treat it as a saved hair look /
an item the user bought. Run:
  `python scripts/capture_image.py --image "<mediaPath>" --source "<URL if any>" --title "<short title if caption>"`
Category stays `hairstyle`; the user tags the ACCESSORY (wig, wig-headband, clip-in, hairpiece) to mark what she owns.
An ETSY/shop product LINK with no image is captured like a normal web page (listing photo = thumbnail).
A photo + link together: use the photo as the image and pass the link as `--source`.

**Note on reliability:** the gateway must run under the Windows scheduled task "OpenClaw Gateway" with the Python Scripts dir on PATH so the
`claude` CLI resolves. Scripts apply_tags.py / add_note.py target the most-recent REAL card (they skip `_`-prefixed
files like the Zoottelkeeper index). build_gallery.py auto-rebuilds the phone gallery after each capture/tag.
