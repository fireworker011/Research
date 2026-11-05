#!/usr/bin/env bash
# M1〜M12。使い方: check_video.sh <mp4> <pet|kane>
# M11: 灰色の単色背景のフレームが50%を超えたらFAIL。
# M12: 字幕と表の領域だけを見る。帯が無いときは SKIP。40px未満はFAIL。
# ペットも金メモも長さは 8.0〜10.5秒。下書きも完成（--final）も同じ範囲。
# 完成だけ 10.500±0.050 にする等値判定は使わない。
# 下書き（--final なし）は音声が無くても M6 と M8 を不合格にしない。
# 完成mp4は --final 必須。--final のとき音声が無い、aac でない、mean_volume が -45dB 以下なら不合格。
# 引数が .md のときは cuts-for-pc.md を見る（tools/check_cuts.py）。
set -euo pipefail

say() {
  local id="$1" ok="$2" detail="$3"
  if [[ "$ok" == "1" ]]; then
    printf '%s\tPASS\t%s\n' "$id" "$detail"
  else
    printf '%s\tFAIL\t%s\n' "$id" "$detail"
    fail=1
  fi
}

# Cygwin の read は最後のフィールドに \r を残す。skip のまま -lt すると算術エラーになり、M12 が PASS になる。
emit_m12() {
  local text_min=$1
  text_min=${text_min//$'\r'/}
  text_min=${text_min//$'\n'/}
  if [[ "$text_min" == "skip" ]]; then
    printf 'M12\tSKIP\t字幕と表の領域に文字の帯が無い\n'
  elif [[ -z "$text_min" || "$text_min" == *[!0-9]* ]]; then
    say M12 0 "文字の高さが数値でない（${text_min}）"
  elif [[ "$text_min" -lt 40 ]]; then
    say M12 0 "最小の文字の高さが${text_min}px（40px未満）"
  else
    say M12 1 "最小の文字の高さは${text_min}px"
  fi
}

if [[ "${1:-}" == "--m12-fixture" ]]; then
  fail=0
  emit_m12 "${2-}"
  exit "$fail"
fi

FINAL=0
if [[ $# -eq 3 && "$3" == "--final" ]]; then
  FINAL=1
elif [[ $# -ne 2 ]]; then
  echo "usage: check_video.sh <mp4> <pet|kane> [--final]" >&2
  exit 2
fi
FILE="$1"
LANE="$2"
fail=0

if [[ "$FILE" == *.md ]]; then
  python3 "$(dirname "$0")/check_cuts.py" "$FILE" "$LANE"
  exit $?
fi

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

if [[ "$LANE" != "pet" && "$LANE" != "kane" ]]; then
  echo "lane は pet か kane: $LANE" >&2
  exit 2
fi
# M5 は下書きも --final も 8.0〜10.5秒。ペットと金メモで範囲を分けない。
lo=8.0
hi=10.5
if [[ "$FINAL" == "1" ]]; then
  label="8.0〜10.5秒（完成）"
else
  label="8.0〜10.5秒"
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

if [[ "$FINAL" == "1" ]]; then
  if [[ "$acodec" == "aac" ]]; then
    say M6 1 "音声=aac"
  else
    say M6 0 "音声=${acodec:-なし}（完成はaac必須）"
  fi
elif [[ -z "$acodec" ]]; then
  say M6 1 "音声なし（下書きは音を入れない）"
elif [[ "$acodec" == "aac" ]]; then
  say M6 1 "音声=aac"
else
  say M6 0 "音声=${acodec}"
fi

if [[ "$pix" == "yuv420p" ]]; then
  say M7 1 "pix_fmt=yuv420p"
else
  say M7 0 "pix_fmt=${pix}"
fi

if [[ -z "$acodec" ]]; then
  if [[ "$FINAL" == "1" ]]; then
    say M8 0 "音声トラックが無い（完成mp4は --final 必須）"
  else
    say M8 1 "音声トラックなし（等倍の声はPCで付ける）"
  fi
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

# M11: 灰色の単色背景のフレームが全体の50%を超えたらFAIL
# M12: 見つけた文字の最小の高さが40px未満ならFAIL
read -r gray_fail text_min < <(python3 - "$FILE" << 'PY'
import subprocess
import sys

path = sys.argv[1]
nb = subprocess.check_output(
    [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=nb_frames", "-of", "csv=p=0", path,
    ],
    text=True,
).strip()
try:
    total = int(nb)
except ValueError:
    total = 252
if total < 1:
    total = 1
indexes = [int(i * (total - 1) / 7) for i in range(8)]
gray_frames = 0
heights = []
for index in indexes:
    raw = subprocess.check_output(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", path, "-vf", f"select=eq(n\\,{index})", "-frames:v", "1",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ]
    )
    width = 1080
    height = 1920
    if len(raw) != width * height * 3:
        width = int(subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width", "-of", "csv=p=0", path],
            text=True,
        ))
        height = int(subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=height", "-of", "csv=p=0", path],
            text=True,
        ))
    step = 4
    gray = 0
    seen = 0
    text_rows = []
    for y in range(height):
        row_text = 0
        for x in range(0, width, step):
            i = (y * width + x) * 3
            r, g, b = raw[i], raw[i + 1], raw[i + 2]
            seen += 1
            if abs(r - g) < 15 and abs(g - b) < 15 and 60 <= r <= 170:
                gray += 1
            else:
                row_text += 1
        table = 0.25 * height <= y < 0.73 * height
        subtitle = 0.78 * height <= y < 0.98 * height
        if row_text > 4 and (table or subtitle):
            text_rows.append(y)
    if seen and gray / seen > 0.90:
        gray_frames += 1
    if text_rows:
        start = prev = text_rows[0]
        bands = []
        for y in text_rows[1:]:
            if y <= prev + 3:
                prev = y
            else:
                bands.append(prev - start + 1)
                start = prev = y
        bands.append(prev - start + 1)
        heights.extend(band for band in bands if 8 <= band <= 200)
gray_fail = 1 if gray_frames / len(indexes) > 0.50 else 0
text_min = str(min(heights)) if heights else "skip"
print(f"{gray_fail} {text_min}")
PY
)

if [[ "$gray_fail" == "1" ]]; then
  say M11 0 "灰色の単色背景のフレームが50%を超える"
else
  say M11 1 "灰色の単色背景のフレームは50%以下"
fi

emit_m12 "$text_min"

# M13: 腕の比率。猫しか映っていない動画は対象外。
# M14: 頭のない塗り、または体の外の黒い塊があればFAIL。
read -r arm_fail head_fail black_fail cat_only < <(python3 - "$FILE" << 'PY'
import subprocess, sys
path = sys.argv[1]
probe = subprocess.check_output([
    "ffprobe", "-v", "error", "-select_streams", "v:0",
    "-show_entries", "format=duration", "-of", "csv=p=0", path,
], text=True).strip()
duration = float(probe or "10.5")
times = [duration * i / 7 for i in range(8)]
arm_fail = 0
head_fail = 0
black_fail = 0
cat_frames = 0
frames = 0

def component_sizes(grid, minimum):
    hh, ww = len(grid), len(grid[0])
    seen = [[False] * ww for _ in range(hh)]
    sizes = []
    for y in range(hh):
        for x in range(ww):
            if not grid[y][x] or seen[y][x]:
                continue
            stack = [(y, x)]
            seen[y][x] = True
            count = 0
            while stack:
                cy, cx = stack.pop()
                count += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < hh and 0 <= nx < ww and grid[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            if count >= minimum:
                sizes.append(count)
    return sizes

for ss in times:
    raw = subprocess.check_output([
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-ss", f"{ss:.3f}", "-i", path, "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])
    width, height = 1080, 1920
    if len(raw) != width * height * 3:
        continue
    frames += 1
    br, bg, bb = raw[0], raw[1], raw[2]
    y0, y1 = int(0.18 * height), int(0.82 * height)
    step = 6
    cols = list(range(0, width, step))
    rows = list(range(y0, y1, step))
    mask = []
    dark = []
    fg_n = 0
    dark_n = 0
    skin_n = 0
    for y in rows:
        row = []
        drow = []
        for x in cols:
            i = (y * width + x) * 3
            r, g, b = raw[i], raw[i + 1], raw[i + 2]
            fg = abs(r - br) > 28 or abs(g - bg) > 28 or abs(b - bb) > 28
            is_dark = max(r, g, b) < 40
            row.append(fg)
            drow.append(fg and is_dark)
            if fg:
                fg_n += 1
                if is_dark:
                    dark_n += 1
                if r > 150 and g > 90 and b < 130 and r > g + 15:
                    skin_n += 1
        mask.append(row)
        dark.append(drow)
    if fg_n >= 30 and dark_n / fg_n >= 0.62 and skin_n < 6:
        cat_frames += 1
    blobs = []
    hh, ww = len(mask), len(mask[0])
    seen = [[False] * ww for _ in range(hh)]
    for y in range(hh):
        for x in range(ww):
            if not mask[y][x] or seen[y][x]:
                continue
            stack = [(y, x)]
            seen[y][x] = True
            pts = []
            while stack:
                cy, cx = stack.pop()
                pts.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < hh and 0 <= nx < ww and mask[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            if len(pts) < 12:
                continue
            ys = [p[0] for p in pts]
            xs = [p[1] for p in pts]
            bh = max(ys) - min(ys) + 1
            bw = max(xs) - min(xs) + 1
            ratio = max(bw, bh) / max(1, min(bw, bh))
            blobs.append(ratio)
    if any(ratio >= 5.5 for ratio in blobs):
        arm_fail = 1
    if len(blobs) >= 2 and any(ratio >= 2.2 for ratio in blobs):
        head_fail = 1
    dark_sizes = component_sizes(dark, 8)
    if dark_sizes:
        body = max(dark_sizes)
        if body < 40 or len(dark_sizes) > 1:
            black_fail = 1
cat_only = 1 if frames and cat_frames == frames else 0
print(f"{arm_fail} {head_fail} {black_fail} {cat_only}")
PY
)
if [[ "$cat_only" == "1" ]]; then
  printf 'M13\tSKIP\t猫だけの映像は対象外\n'
elif [[ "$arm_fail" == "1" ]]; then
  say M13 0 "腕の比率の外れ値が1コマ以上"
else
  say M13 1 "腕の比率の外れ値なし"
fi
if [[ "$black_fail" == "1" ]]; then
  say M14 0 "体の外に黒い塊がある"
elif [[ "$head_fail" == "1" ]]; then
  say M14 0 "塗りのかたまりが2つ以上で、頭のないかたまりがある"
else
  say M14 1 "頭のない塗りのかたまりなし"
fi

exit "$fail"
