#!/bin/sh
# 12本を、口位置を確認した絵で書き出す。投稿はしない。
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
REPO="$(CDPATH= cd -- "$ROOT/.." && pwd)"
TOOL="$REPO/tools/irasutoya-short"
PY="${IRASUTOYA_PYTHON:-python3}"
export IRASUTOYA_VOICEVOX="${IRASUTOYA_VOICEVOX:-$HOME/.cache/irasutoya-short/voicevox}"
cd "$TOOL"
fail=0
for brief in "$ROOT"/[0-9][0-9]-*/brief.json; do
  slug="$(basename "$(dirname "$brief")")"
  work="${IRASUTOYA_WORK:-/tmp/irasu-work}/$slug"
  out="$ROOT/$slug/out.mp4"
  echo "== $slug =="
  if ! PYTHONPATH=. "$PY" -m irasutoya_short make "$brief" --work "$work" --out "$out"; then
    echo "FAILED $slug" >&2
    fail=1
    continue
  fi
  cp "$work/REPORT.json" "$ROOT/$slug/REPORT.json"
  cp "$work/project.json" "$ROOT/$slug/project.json"
done
if [ "$fail" -ne 0 ]; then
  exit 1
fi
PYTHONPATH=. "$PY" "$ROOT/extract_qa.py" "$ROOT"
echo "rendered. QA frames are in each video folder. Do not upload."
