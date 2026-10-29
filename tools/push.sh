#!/usr/bin/env bash
# Publish the current files as a single fresh commit on main.
# History is replaced each time so deleted episodes don't pile up and
# push the repository past GitHub's size limits.
set -euo pipefail
cd "$(dirname "$0")/.."
msg="${1:-Update podcast feed}"
git checkout -q --orphan publish-tmp
git add -A
git -c user.name="Claude" -c user.email="noreply@anthropic.com" \
  commit -q -m "$msg" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XXm1J1qkBMapBNoPLQaKL1"
git branch -q -D main 2>/dev/null || true
git branch -q -m main
git push -q --force origin main
echo "Pushed. Feed: https://vinceplanetta-oss.github.io/Podcasts/feed.xml"
