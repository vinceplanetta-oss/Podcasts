#!/usr/bin/env python3
"""Add an MP3 episode to Vince's private podcast feed and rebuild feed.xml.

Usage:
  python3 tools/publish.py add path/to/episode.mp3 --title "Title" [--description "..."]
  python3 tools/publish.py remove <episode-file-name.mp3>
  python3 tools/publish.py rebuild

After running, push with: bash tools/push.sh "commit message"
"""
import argparse, datetime as dt, email.utils, html, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EP_DIR = os.path.join(ROOT, "episodes")
DB = os.path.join(ROOT, "episodes.json")
FEED = os.path.join(ROOT, "feed.xml")
BASE_URL = "https://vinceplanetta-oss.github.io/Podcasts"
SIZE_CAP = 700 * 1024 * 1024   # GitHub Pages sites are limited to 1 GB; stay well under
MAX_KBPS = 96                  # re-encode anything above this to 64 kbps mono (speech)

CHANNEL = {
    "title": "Vince's Podcasts",
    "description": "Private podcasts made by Claude for Vince.",
    "author": "Vince Planetta",
}


def load():
    if os.path.exists(DB):
        with open(DB) as f:
            return json.load(f)
    return []


def save(eps):
    with open(DB, "w") as f:
        json.dump(eps, f, indent=2)


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,bit_rate",
         "-of", "json", path], capture_output=True, text=True, check=True).stdout
    fmt = json.loads(out)["format"]
    return float(fmt["duration"]), int(fmt.get("bit_rate", 0)) // 1000


def slug(s):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:60] or "episode"


def add(src, title, description):
    os.makedirs(EP_DIR, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)
    name = f"{now:%Y%m%d-%H%M}-{slug(title)}.mp3"
    dest = os.path.join(EP_DIR, name)
    # Always re-encode to 44.1 kHz, 64 kbps constant bitrate mono MP3. The Light Phone
    # player crashes on some files at other sample rates (e.g. 24 kHz TTS output).
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-ac", "1", "-ar", "44100",
                    "-b:a", "64k", "-map_metadata", "-1", "-id3v2_version", "3", dest], check=True)
    dur, _ = probe(dest)
    eps = load()
    eps.append({
        "file": name, "title": title, "description": description or title,
        "pubDate": email.utils.format_datetime(now), "bytes": os.path.getsize(dest),
        "duration": int(round(dur)),
    })
    prune(eps)
    save(eps)
    build(eps)
    print(f"Added {name} ({os.path.getsize(dest)/1e6:.1f} MB, {dur/60:.1f} min)")


def prune(eps):
    # Drop the oldest episodes until the total size is under the cap.
    while len(eps) > 1 and sum(e["bytes"] for e in eps) > SIZE_CAP:
        old = eps.pop(0)
        p = os.path.join(EP_DIR, old["file"])
        if os.path.exists(p):
            os.remove(p)
        print(f"Pruned oldest episode: {old['title']}")


def remove(name):
    eps = [e for e in load() if e["file"] != name]
    p = os.path.join(EP_DIR, name)
    if os.path.exists(p):
        os.remove(p)
    save(eps)
    build(eps)
    print(f"Removed {name}")


def build(eps):
    esc = html.escape
    items = []
    for e in reversed(eps):  # newest first
        url = f"{BASE_URL}/episodes/{e['file']}"
        h, rem = divmod(e["duration"], 3600)
        m, s = divmod(rem, 60)
        items.append(f"""    <item>
      <title>{esc(e['title'])}</title>
      <description>{esc(e['description'])}</description>
      <enclosure url="{esc(url)}" length="{e['bytes']}" type="audio/mpeg"/>
      <guid isPermaLink="false">{esc(e['file'])}</guid>
      <pubDate>{e['pubDate']}</pubDate>
      <itunes:duration>{h:02d}:{m:02d}:{s:02d}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
    </item>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{esc(CHANNEL['title'])}</title>
    <link>{BASE_URL}/</link>
    <atom:link href="{BASE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>{esc(CHANNEL['description'])}</description>
    <language>en-us</language>
    <itunes:author>{esc(CHANNEL['author'])}</itunes:author>
    <itunes:explicit>false</itunes:explicit>
    <itunes:block>Yes</itunes:block>
{chr(10).join(items)}
  </channel>
</rss>
"""
    with open(FEED, "w") as f:
        f.write(feed)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("mp3"); a.add_argument("--title", required=True)
    a.add_argument("--description", default="")
    r = sub.add_parser("remove"); r.add_argument("file")
    sub.add_parser("rebuild")
    args = ap.parse_args()
    if args.cmd == "add":
        add(args.mp3, args.title, args.description)
    elif args.cmd == "remove":
        remove(args.file)
    else:
        build(load())


if __name__ == "__main__":
    sys.exit(main())
