# Vince's podcast feed

**This repository is ONLY for the podcast feed.** Do not use it to host temporary files
(website photos, Wix uploads, anything else), and never commit a tree that drops feed.xml,
episodes.json or episodes/. On 2026-10-12 a Wix photo upload replaced the whole repo and
wiped every episode, which made the Light Phone player crash. Use a separate repository
for anything that isn't a podcast episode.

This repository is a private podcast RSS feed served by GitHub Pages. Vince listens on a
Light Phone 3, whose Podcast tool is subscribed to:

https://vinceplanetta-oss.github.io/Podcasts/feed.xml

The Podcast tool stops when an episode ends and remembers his place, which the Music tool
does not. That is the whole reason this exists.

## Adding a podcast you made for Vince

1. Make the MP3 as usual (female voice, about 25 minutes).
2. From the repo root:

   python3 tools/publish.py add /path/to/episode.mp3 --title "Episode title" --description "One line summary"
   bash tools/push.sh "Add episode: Episode title"

3. Tell Vince it's published. It appears on his Light Phone after GitHub Pages rebuilds
   (usually a minute or two) and the Light dashboard next checks the feed.

## Notes

- episodes.json is the source of truth; feed.xml is generated from it. Don't hand edit feed.xml.
- publish.py re-encodes every file to 44.1 kHz 64 kbps mono (other sample rates crash the
  Light Phone player) and drops the oldest episodes once
  the total passes 700 MB, because GitHub Pages sites are capped at 1 GB.
- push.sh replaces history with one fresh commit on every publish so removed MP3s don't keep
  growing the repository. Force pushing main is expected here.
- To remove an episode: python3 tools/publish.py remove <file name>, then push.sh.
- The repository is public (free GitHub Pages needs that). Vince knows and agreed.
