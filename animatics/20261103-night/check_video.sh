#!/usr/bin/env bash
# M1〜M10。使い方: check_video.sh <mp4> <pet|kane>
# ペットの長さは 8〜50秒。金メモの長さは 8〜60秒。
# 2026-11-02の記録では金メモは 12〜60秒だった。
# 2026-11-04の指示は書き出しを 10.5秒にする。12秒未満を落とすと、その指示と同時に PASS にならない。
# この検査の金メモの下限は 8秒。
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: check_video.sh <mp4> <pet|kane>" >&2
  exit 2
fi
FILE="$1"
LANE="$2"
fail=0

say() {
  local id="$1" ok="$2" detail="$3"
  if [[ "$ok" == "1" ]]; then
    printf '%s\tPASS\t%s\n' "$id" "$detail"
  else
    printf '%s\tFAIL\t%s\n' "$id" "$detail"
    fail=1
  fi
}

fmt=$(ffprobe -v error -show_entries format=format_name,duration -of default=nw=1:nk=1 "$FILE" | tr '\n' ' ')
format_name=$(ffprobe -v error -show_entries format=format_name -of csv=p=0 "$FILE" | tr -d '"')
duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FILE")
vfield() {
  ffprobe -v error -select_streams v:0 -show_entries "stream=$1" -of csv=p=0 "$FILE" | tr -d '"'
}
codec=$(vfield codec_name)
width=$(vfield width)
height=$(vfield height)
fps=$(vfield avg_frame_rate)
pix=$(vfield pix_fmt)
acodec=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of csv=p=0 "$FILE" || true)

case "$format_name" in
  *mp4*|*mov*) say M1 1 "コンテナ=${format_name}（mp4系）" ;;
  *) say M1 0 "コンテナ=${format_name}" ;;
esac

if [[ "$codec" == "h264" ]]; then
  say M2 1 "映像コーデック=h264（許可: h264）"
else
  say M2 0 "映像コーデック=${codec}"
fi

if [[ "$width" == "1080" && "$height" == "1920" ]]; then
  say M3 1 "解像度=1080x1920"
else
  say M3 0 "解像度=${width}x${height}"
fi

fps_num=${fps%/*}
fps_den=${fps#*/}
if [[ "$fps_den" == "$fps" ]]; then
  fps_val="$fps_num"
else
  fps_val=$(python3 -c "print(float('$fps_num')/float('$fps_den'))")
fi
if python3 - "$fps_val" << 'PY'
import sys
sys.exit(0 if abs(float(sys.argv[1]) - 24) < 0.05 else 1)
PY
then
  say M4 1 "fps=24.00"
else
  say M4 0 "fps=${fps}"
fi

if [[ "$LANE" == "pet" ]]; then
  lo=8; hi=50; label="8〜50秒"
elif [[ "$LANE" == "kane" ]]; then
  lo=8; hi=60; label="8〜60秒"
else
  echo "lane は pet か kane: $LANE" >&2
  exit 2
fi
if python3 - "$duration" "$lo" "$hi" << 'PY'
import sys
d, lo, hi = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
sys.exit(0 if lo <= d <= hi else 1)
PY
then
  say M5 1 "長さ=${duration}秒（${label}）"
else
  say M5 0 "長さ=${duration}秒（${label}）"
fi

if [[ "$acodec" == "aac" ]]; then
  say M6 1 "音声=aac"
else
  say M6 0 "音声=${acodec:-なし}（aac必須）"
fi

if [[ "$pix" == "yuv420p" ]]; then
  say M7 1 "pix_fmt=yuv420p"
else
  say M7 0 "pix_fmt=${pix}"
fi

if [[ -z "$acodec" ]]; then
  say M8 0 "音声トラックが無いので測れない"
else
  vol=$(ffmpeg -hide_banner -i "$FILE" -af volumedetect -f null - 2>&1 | sed -n 's/.*mean_volume: //p' | tail -1)
  mean=${vol% dB}
  if python3 - "$mean" << 'PY'
import sys
sys.exit(0 if float(sys.argv[1]) > -45 else 1)
PY
  then
    say M8 1 "無音でない mean_volume=${vol}"
  else
    say M8 0 "無音に近い mean_volume=${vol}"
  fi
fi

black=$(ffmpeg -hide_banner -t 1 -i "$FILE" -vf blackdetect=d=0.5:pix_th=0.10 -an -f null - 2>&1 | grep -c 'black_start' || true)
if [[ "$black" == "0" ]]; then
  say M9 1 "冒頭1秒に0.5秒以上の黒画面なし"
else
  say M9 0 "冒頭1秒に黒画面"
fi

if [[ "$height" -gt "$width" ]]; then
  say M10 1 "縦長（9:16）"
else
  say M10 0 "縦長ではない ${width}x${height}"
fi

exit "$fail"
