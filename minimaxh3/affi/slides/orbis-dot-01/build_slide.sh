#!/usr/bin/env bash
# cut-list-ffmpeg wrapper. Does not post. Does not call Imagine.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/../../../.." && pwd)"
OUT="${1:-$ROOT/orbis-dot-01.mp4}"
cd "$REPO"
exec python -m minimaxh3.affi cutlist render \
  --csv "$ROOT/cuts.csv" \
  --out "$OUT" \
  --purpose slide \
  --bgm "$ROOT/bgm/slide.m4a"
