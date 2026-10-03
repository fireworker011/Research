#!/usr/bin/env bash
# Vertical 9:16 still slide. Does not post. Does not call Imagine.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
IMAGES="${1:-$ROOT/images}"
OUT="${2:-$ROOT/orbis-dot-01.mp4}"
BGM="${3:-$ROOT/bgm/slide.m4a}"
SRT="$ROOT/captions.srt"
FONT=""
for c in \
  /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc \
  /usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc \
  /usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc
do
  if [[ -f "$c" ]]; then FONT="$c"; break; fi
done
if [[ -z "$FONT" ]]; then
  echo "日本語フォントが無い。Noto Sans CJK を入れてから実行する。" >&2
  exit 1
fi
FONTDIR="$(dirname "$FONT")"
inputs=()
for name in 01.png 02.png 03.png 04.png 05.png; do
  if [[ ! -f "$IMAGES/$name" ]]; then
    echo "画像が無い: $IMAGES/$name" >&2
    exit 1
  fi
  inputs+=(-loop 1 -t 3.0 -i "$IMAGES/$name")
done
filter=""
for i in 0 1 2 3 4; do
  filter+="[$i:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1[v$i];"
done
filter+="[v0][v1][v2][v3][v4]concat=n=5:v=1:a=0[cat];"
filter+="[cat]subtitles=$SRT:fontsdir=$FONTDIR:force_style='FontName=Noto Sans CJK JP\,FontSize=64\,Alignment=8\,BorderStyle=3\,Outline=0\,BackColour=&H00FFFFFF&\,PrimaryColour=&H00000000&\,MarginV=160'[cap];"
filter+="[cap]drawtext=text='PR':fontsize=36:fontcolor=black:box=1:boxcolor=white:boxborderw=8:x=w-tw-48:y=48[vout]"
mkdir -p "$(dirname "$OUT")"
if [[ -f "$BGM" ]]; then
  ffmpeg -y "${inputs[@]}" -i "$BGM" \
    -filter_complex "$filter" -map "[vout]" -map 5:a \
    -t 15 -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$OUT"
else
  ffmpeg -y "${inputs[@]}" \
    -filter_complex "$filter" -map "[vout]" \
    -t 15 -c:v libx264 -pix_fmt yuv420p -an "$OUT"
fi
echo "$OUT"
