#!/bin/bash
# build_audio → render_frames → verify_mp4 → check_pr_badge
set -euo pipefail
cd "$(dirname "$0")"
DAY="${1:?day name}"
JOB="${2:?job json}"
ROOT="$(pwd)"
AUDIO="$ROOT/out/audio_$DAY"
OUT="$ROOT/out"
REPORT="$OUT/report_$DAY"
mkdir -p "$AUDIO" "$OUT" "$REPORT"
python3 src/build_audio.py --job "$JOB" --speaker 13 --out-dir "$AUDIO"
JOB_ID="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1],encoding='utf-8'))['job_id'])" "$JOB")"
MP4="$OUT/${JOB_ID}.mp4"
python3 src/render_frames.py --job "$JOB" --timing "$AUDIO/audio_timing.json" --audio "$AUDIO/master_audio.wav" --out "$MP4"
python3 tools/verify_mp4.py --video "$MP4" --job "$JOB" --timing "$AUDIO/audio_timing.json" --write --report-dir "$REPORT"
EXPECT="$(python3 -c "import json,sys; print('true' if json.load(open(sys.argv[1],encoding='utf-8')).get('pr_badge') else 'false')" "$JOB")"
python3 tools/check_pr_badge.py --video "$MP4" --expect "$EXPECT" --report "$REPORT/pr_check.json"
