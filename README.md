# beauty-librarian

An OpenClaw agent skill that captures hair / makeup / hijab style references - pasted text, a blog
tutorial, a YouTube video or a Short - into an Obsidian "Beauty Library" as tagged markdown cards with a
thumbnail. A video that demos several looks is split into one entry per look, each deep-linked to its
timestamp. A gallery script builds a visual "lookbook" page from the library.

## Status
Core capture, tagging, deep-link and gallery scripts work. Agent-side extraction (blog parsing, splitting
long videos into looks, tagging quality) depends on the agent and needs tuning on real tutorials.

## How it runs
1. **Trigger.** A message to your OpenClaw Telegram bot (a tutorial link or text, or anything tagged
   `#beauty`), or any post in your Telegram "Beauty Library Channel" (set the channel id in SKILL.md).
2. **Fetch.** The agent routes by source: pasted text is used as-is; web pages are fetched and read;
   YouTube / Shorts use `yt-dlp` for transcript, chapters and thumbnail (try without cookies first).
3. **Assemble.** The agent splits multi-look videos, picks tags from `vocab.json` (closed facets only from
   the list; open facets may propose new values, logged to `proposed_tags.log`), and builds one JSON entry
   per look.
4. **Write.** `scripts/capture.py` writes one markdown file per look into `library_dir`, with all facets in
   frontmatter, a flat tag list and the thumbnail. Images go through `scripts/capture_image.py`.
5. **Inbox sweep.** `enrich.sh` (run on a schedule/heartbeat) processes bare link-notes dropped in
   `_BeautyInbox` and rebuilds the lookbook with `scripts/build_gallery.py`.
6. **Review.** `scripts/tag_review.py --library <library_dir>` reports new and near-duplicate tags monthly.
   `scripts/apply_tags.py` and `scripts/add_note.py` apply follow-up tags / notes to an existing entry.

## Setup
- Python 3, `yt-dlp` on PATH (`ffmpeg` optional, only for clipping).
- Copy the folder into your OpenClaw skills folder.
- Replace the placeholders: `C:/Users/YOU/...` paths (or set `BEAUTY_LIB` where supported),
  `@YourOpenClawBot`, and `<YOUR_TELEGRAM_CHANNEL_ID>`.
- Edit `vocab.json` to change tags (lowercase-hyphenated). No code change needed.
- Optional Capacities push reads `CAPACITIES_API_KEY` / `CAPACITIES_SPACE_ID` from the environment
  (off by default).
