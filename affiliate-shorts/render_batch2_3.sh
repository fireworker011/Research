#!/bin/sh
# batch2 と batch3 の残り。見本3本の確認が済むまで回さない。投稿はしない。
set -eu
if [ "${IRASUTOYA_RENDER_ALL:-}" != "1" ]; then
  echo "見本の確認前なので、残りは書き出さない。承認後に IRASUTOYA_RENDER_ALL=1 を付けて実行する。" >&2
  exit 1
fi
ROOT="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
REPO="$(CDPATH= cd -- "$ROOT/.." && pwd)"
TOOL="$REPO/tools/irasutoya-short"
PY="${IRASUTOYA_PYTHON:-python3}"
export IRASUTOYA_VOICEVOX="${IRASUTOYA_VOICEVOX:-$HOME/.cache/irasutoya-short/voicevox}"
cd "$TOOL"
fail=0
for brief in "$ROOT"/batch2/*/brief.json "$ROOT"/batch3/*/brief.json; do
  slug="$(basename "$(dirname "$brief")")"
  batch="$(basename "$(dirname "$(dirname "$brief")")")"
  work="${IRASUTOYA_WORK:-/tmp/irasu-work}/$slug"
  out="$ROOT/$batch/$slug/out.mp4"
  echo "== $batch/$slug =="
  if ! PYTHONPATH=. "$PY" -m irasutoya_short picture-first "$brief" --work "$work" --out "$out"; then
    echo "FAILED $slug" >&2
    fail=1
    continue
  fi
  cp "$work/REPORT.json" "$ROOT/$batch/$slug/REPORT.json"
  cp "$work/project.json" "$ROOT/$batch/$slug/project.json"
done
if [ "$fail" -ne 0 ]; then
  exit 1
fi
PYTHONPATH=. "$PY" "$ROOT/extract_qa.py" "$ROOT/batch2"
PYTHONPATH=. "$PY" "$ROOT/extract_qa.py" "$ROOT/batch3"
echo "rendered. QA frames are in each video folder. Do not upload."
