#!/usr/bin/env bash
# Cloud Agent install for the affiliate-engine (zero npm dependencies, Node 20+).
# Idempotent: safe to run repeatedly and against cached/snapshot state.
set -euo pipefail

# System packages for the OPTIONAL Shorts/Reels generator (src/video-semi-auto.js):
# ffmpeg renders the video, Noto CJK renders Japanese text. The core automated
# pipeline (strategy/post/report/insight/video-judge) needs only Node.
NOTO_TTC=/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc
if ! command -v ffmpeg >/dev/null 2>&1 || [ ! -f "$NOTO_TTC" ]; then
  echo "Installing ffmpeg + Noto CJK fonts..."
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    ffmpeg fonts-noto-cjk fontconfig
else
  echo "ffmpeg and Noto CJK fonts already present; skipping apt."
fi

cd "$(dirname "$0")/../affiliate-engine"

echo "Node: $(node --version)   ffmpeg: $(ffmpeg -version 2>/dev/null | head -1)"

# No dependencies to install. Sanity-check every source file compiles.
for f in src/*.js; do
  node --check "$f"
done
echo "All $(ls src/*.js | wc -l | tr -d ' ') source files pass syntax check."

# Built-in self-test for the video cash-loop judge.
node src/video-judge.js --self-test

echo "affiliate-engine install complete."
