#!/usr/bin/env bash
# Join Imagine clips, then fit the voice to that picture.
# Picture length starts as the shot lengths in IMAGINE.md.
# STYLE.md may hold the last frame so the length reaches that pack's L band.
# The voice is sped up only when it does not fit. The picture is not recut to the voice.
# BGM follows STYLE.md (B1 is silence). --bgm replaces that bed. Amplitude 0.15.
# A no-BGM file is always written. Captions are not burned in. Text is on thumb.png.
# Style QA is style_matrix.py: at most 2 shared axes with the previous video,
# at most 3 with any of the last 5, never an exact match. See STYLE-VARIATION.md.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

usage() {
  cat <<'EOF'
usage: finish.sh PACK_DIR [--bgm FILE] [--clips DIR] [--voice FILE] [--out DIR]
       finish.sh --self-test

PACK_DIR   shorts-stock/2026-10-13/pet/01-gray-blink
--bgm      歌詞の無い曲。渡したときだけ BGM 版を書く。振幅 0.15。
--clips    既定は PACK_DIR/imagine 。 shot-01.mp4 から IMAGINE.md の順。
--voice    既定は PACK_DIR/voice/narration.wav 。ナレーション無しの本は使わない。
--out      既定は PACK_DIR/out
--self-test  色のプレースホルダで結合、声、BGM、9:16 を確認し、サンプルを1本 samples/ に置く。
EOF
}

SELF_TEST=0
BGM=""
CLIPS=""
VOICE_FILE=""
OUT=""
PACK=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --self-test) SELF_TEST=1; shift ;;
    --bgm) BGM=${2:?}; shift 2 ;;
    --clips) CLIPS=${2:?}; shift 2 ;;
    --voice) VOICE_FILE=${2:?}; shift 2 ;;
    --out) OUT=${2:?}; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    --) shift; break ;;
    -*) echo "不明な引数: $1" >&2; usage; exit 2 ;;
    *) PACK=$1; shift ;;
  esac
done

abs_path() {
  python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$1"
}

probe_duration() {
  ffprobe -v error -show_entries format=duration -of csv=p=0 "$1"
}

has_audio() {
  local n
  n=$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$1" | wc -l)
  [[ "$n" -gt 0 ]]
}

mix_voice() {
  local picture=$1 bed=$2 voice=$3 fit=$4 bgm=$5 dest=$6 picture_sec=$7
  local filter vfilter
  if [[ -n "$voice" ]]; then
    vfilter=$(python3 - "$fit" "$picture_sec" <<'PY'
import json, sys
fit = json.loads(sys.argv[1])
picture = sys.argv[2]
delay = int(round(float(fit["start_sec"]) * 1000))
parts = ["aresample=48000", "aformat=channel_layouts=stereo"]
if fit["atempo_filter"]:
    parts.append(fit["atempo_filter"])
parts.append(f"adelay={delay}|{delay}")
parts.append(f"apad=whole_dur={picture}")
parts.append(f"atrim=0:{picture}")
print(",".join(parts))
PY
)
    if [[ -n "$bgm" ]]; then
      filter="[1:a]aformat=channel_layouts=stereo,aresample=48000,volume=1.0[bed];[2:a]${vfilter}[voice];[3:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.15,apad=whole_dur=${picture_sec},atrim=0:${picture_sec}[bgm];[bed][voice][bgm]amix=inputs=3:duration=first:dropout_transition=0:normalize=0[a]"
      ffmpeg -y -nostdin -loglevel error -i "$picture" -i "$bed" -i "$voice" -stream_loop -1 -i "$bgm" \
        -filter_complex "$filter" -map 0:v -map "[a]" \
        -c:v copy -c:a aac -b:a 160k -movflags +faststart "$dest"
    else
      filter="[1:a]aformat=channel_layouts=stereo,aresample=48000,volume=1.0[bed];[2:a]${vfilter}[voice];[bed][voice]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
      ffmpeg -y -nostdin -loglevel error -i "$picture" -i "$bed" -i "$voice" \
        -filter_complex "$filter" -map 0:v -map "[a]" \
        -c:v copy -c:a aac -b:a 160k -movflags +faststart "$dest"
    fi
  elif [[ -n "$bgm" ]]; then
    filter="[1:a]aformat=channel_layouts=stereo,aresample=48000,volume=1.0[bed];[2:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.15,apad=whole_dur=${picture_sec},atrim=0:${picture_sec}[bgm];[bed][bgm]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
    ffmpeg -y -nostdin -loglevel error -i "$picture" -i "$bed" -stream_loop -1 -i "$bgm" \
      -filter_complex "$filter" -map 0:v -map "[a]" \
      -c:v copy -c:a aac -b:a 160k -movflags +faststart "$dest"
  else
    filter="[1:a]aformat=channel_layouts=stereo,aresample=48000,volume=1.0,apad=whole_dur=${picture_sec},atrim=0:${picture_sec}[a]"
    ffmpeg -y -nostdin -loglevel error -i "$picture" -i "$bed" \
      -filter_complex "$filter" -map 0:v -map "[a]" \
      -c:v copy -c:a aac -b:a 160k -movflags +faststart "$dest"
  fi
}

finish_one() {
  local pack clips voice_override out bgm
  pack=$(abs_path "$1")
  clips=${2:-$pack/imagine}
  voice_override=${3:-}
  out=${4:-$pack/out}
  bgm=${5:-}
  if [[ ! -f "$pack/IMAGINE.md" ]]; then
    echo "IMAGINE.md が無い: $pack" >&2
    exit 1
  fi
  mkdir -p "$out"
  local work
  work=$(mktemp -d)
  python3 "$ROOT/pack_meta.py" dump "$pack" >"$work/meta.json"

  python3 - "$work/meta.json" "$clips" "$work/shots.tsv" <<'PY'
import json, sys
from pathlib import Path
meta = json.loads(Path(sys.argv[1]).read_text())
clips = Path(sys.argv[2])
rows = []
for shot in meta["shots"]:
    src = clips / Path(shot["file"]).name
    if not src.is_file():
        raise SystemExit(f"クリップが無い: {src}")
    rows.append(f"{shot['length_sec']}\t{src}")
Path(sys.argv[3]).write_text("\n".join(rows) + "\n")
PY

  local list_v="$work/video.txt"
  local list_a="$work/audio.txt"
  : >"$list_v"
  : >"$list_a"
  local i=0
  while IFS=$'\t' read -r length src <&3; do
    i=$((i + 1))
    local src_dur pad part_v part_a
    src_dur=$(probe_duration "$src")
    pad=$(python3 -c 'import sys; print(max(0.0, float(sys.argv[1]) - float(sys.argv[2])) + (1.0/30.0))' "$length" "$src_dur")
    part_v="$work/v$(printf '%02d' "$i").mp4"
    part_a="$work/a$(printf '%02d' "$i").wav"
    ffmpeg -y -nostdin -loglevel error -i "$src" \
      -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,fps=30,format=yuv420p,tpad=stop_mode=clone:stop_duration=${pad}" \
      -t "$length" -an \
      -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -r 30 -video_track_timescale 30000 \
      "$part_v"
    if has_audio "$src"; then
      ffmpeg -y -nostdin -loglevel error -i "$src" -vn \
        -af "aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur=${length},atrim=0:${length}" \
        -t "$length" -ar 48000 -ac 2 "$part_a"
    else
      ffmpeg -y -nostdin -loglevel error -f lavfi -i "anullsrc=r=48000:cl=stereo" -t "$length" -ar 48000 -ac 2 "$part_a"
    fi
    printf "file '%s'\n" "$part_v" >>"$list_v"
    printf "file '%s'\n" "$part_a" >>"$list_a"
  done 3<"$work/shots.tsv"

  ffmpeg -y -nostdin -loglevel error -f concat -safe 0 -i "$list_v" -c copy "$work/picture.mp4"
  ffmpeg -y -nostdin -loglevel error -f concat -safe 0 -i "$list_a" -c copy "$work/bed.wav"

  local picture_sec script_sec
  picture_sec=$(probe_duration "$work/picture.mp4")
  script_sec=$(python3 -c 'import json,sys; from pathlib import Path; m=json.loads(Path(sys.argv[1]).read_text()); print(sum(s["length_sec"] for s in m["shots"]))' "$work/meta.json")
  python3 -c 'import sys; d=abs(float(sys.argv[1])-float(sys.argv[2])); raise SystemExit(0 if d<=0.05 else f"絵の長さがショット合計と違う: {sys.argv[1]} vs {sys.argv[2]}")' \
    "$picture_sec" "$script_sec"

  if [[ -f "$pack/STYLE.md" ]]; then
    python3 "$ROOT/style_matrix.py" plan "$pack" "$script_sec" >"$work/style.json"
    local vf target hook lavfi
    vf=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))["vf"])' "$work/style.json")
    target=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))["target_sec"])' "$work/style.json")
    hook=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))["hook"])' "$work/style.json")
    lavfi=$(python3 -c 'import json,sys; value=json.load(open(sys.argv[1],encoding="utf-8"))["bgm_lavfi"]; print("" if value is None else value)' "$work/style.json")
    ffmpeg -y -nostdin -loglevel error -i "$work/picture.mp4" -vf "$vf" -an \
      -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -r 30 -video_track_timescale 30000 \
      "$work/styled.mp4"
    mv "$work/styled.mp4" "$work/picture.mp4"
    ffmpeg -y -nostdin -loglevel error -i "$work/bed.wav" \
      -af "apad=whole_dur=${target},atrim=0:${target}" -ar 48000 -ac 2 "$work/bed-long.wav"
    mv "$work/bed-long.wav" "$work/bed.wav"
    if [[ "$hook" == "H5" ]]; then
      ffmpeg -y -nostdin -loglevel error -i "$work/bed.wav" -f lavfi -t 0.2 -i "sine=frequency=880:sample_rate=48000" \
        -filter_complex "[1:a]apad=whole_dur=${target},atrim=0:${target},volume=0.4[tick];[0:a][tick]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]" \
        -map "[a]" -ar 48000 -ac 2 "$work/bed-hook.wav"
      mv "$work/bed-hook.wav" "$work/bed.wav"
    fi
    if [[ -z "$bgm" && -n "$lavfi" ]]; then
      ffmpeg -y -nostdin -loglevel error -f lavfi -i "$lavfi" -t "$target" -ar 48000 -ac 2 "$work/style-bgm.wav"
      bgm="$work/style-bgm.wav"
    fi
    picture_sec=$target
  fi

  local voice_wav="" voice_sec="" fit_json="null"
  local narration
  narration=$(python3 -c 'import json,sys; from pathlib import Path; m=json.loads(Path(sys.argv[1]).read_text()); print("yes" if m["voice"]["narration"] else "no")' "$work/meta.json")
  if [[ "$narration" == "yes" ]]; then
    if [[ -n "$voice_override" ]]; then
      voice_wav=$voice_override
    else
      voice_wav="$pack/voice/narration.wav"
    fi
    if [[ ! -f "$voice_wav" ]]; then
      echo "声が無い: $voice_wav" >&2
      exit 1
    fi
    voice_sec=$(probe_duration "$voice_wav")
    fit_json=$(python3 - "$work/meta.json" "$picture_sec" "$voice_sec" <<'PY'
import json, sys
from pathlib import Path
from pack_meta import fit_voice
meta = json.loads(Path(sys.argv[1]).read_text())
voice = meta["voice"]
print(json.dumps(fit_voice(float(sys.argv[2]), float(sys.argv[3]), voice["window_start_sec"], voice["window_end_sec"])))
PY
)
  fi

  local stem
  stem=$(python3 -c 'import json,sys; from pathlib import Path; m=json.loads(Path(sys.argv[1]).read_text()); print(m["date"]+"-"+m["line"]+"-"+m["slug"])' "$work/meta.json")
  local nobgm="$out/${stem}-nobgm.mp4"
  local withbgm="$out/${stem}.mp4"

  mix_voice "$work/picture.mp4" "$work/bed.wav" "$voice_wav" "$fit_json" "" "$nobgm" "$picture_sec"
  if [[ -n "$bgm" ]]; then
    if [[ ! -f "$bgm" ]]; then
      echo "BGM が無い: $bgm" >&2
      exit 1
    fi
    mix_voice "$work/picture.mp4" "$work/bed.wav" "$voice_wav" "$fit_json" "$bgm" "$withbgm" "$picture_sec"
  fi

  python3 - "$work/meta.json" "$fit_json" "$picture_sec" "$voice_sec" "$bgm" "$nobgm" "$withbgm" "$out/${stem}-log.json" <<'PY'
import json, sys
from pathlib import Path
meta = json.loads(Path(sys.argv[1]).read_text())
fit = json.loads(sys.argv[2]) if sys.argv[2] != "null" else None
bgm = sys.argv[5]
log = {
    "pack": meta["rel"],
    "picture_sec": float(sys.argv[3]),
    "shot_sec": [shot["length_sec"] for shot in meta["shots"]],
    "voice_sec": None if not sys.argv[4] else float(sys.argv[4]),
    "fit": fit,
    "bgm": bgm or None,
    "bgm_amplitude": 0.15 if bgm else None,
    "captions": False,
    "nobgm": sys.argv[6],
    "with_bgm": sys.argv[7] if bgm else None,
}
Path(sys.argv[8]).write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
PY

  if [[ "${FINISH_NO_LOG:-}" != "1" && -f "$pack/STYLE.md" ]]; then
    python3 "$ROOT/style_matrix.py" record "$pack" "$picture_sec"
  fi

  rm -rf "$work"
  echo "$nobgm"
  if [[ -n "$bgm" ]]; then
    echo "$withbgm"
  fi
}

assert_frame() {
  python3 - "$1" "$2" <<'PY'
import json, subprocess, sys
file, expect = sys.argv[1], float(sys.argv[2])
raw = subprocess.check_output([
    "ffprobe", "-v", "error", "-show_entries",
    "format=duration:stream=codec_type,width,height", "-of", "json", file,
], text=True)
data = json.loads(raw)
dur = float(data["format"]["duration"])
if abs(dur - expect) > 0.05:
    raise SystemExit(f"{file}: 長さ {dur} が {expect} と違う")
video = [s for s in data["streams"] if s.get("codec_type") == "video"]
audio = [s for s in data["streams"] if s.get("codec_type") == "audio"]
subs = [s for s in data["streams"] if s.get("codec_type") == "subtitle"]
if not video or video[0].get("width") != 1080 or video[0].get("height") != 1920:
    raise SystemExit(f"{file}: 9:16 1080x1920 ではない")
if not audio:
    raise SystemExit(f"{file}: 音声が無い")
if subs:
    raise SystemExit(f"{file}: 字幕ストリームがある")
print(f"ok {file} dur={dur:.3f} 1080x1920")
PY
}

style_target() {
  python3 -c 'import re,sys; text=open(sys.argv[1],encoding="utf-8").read(); print(re.search(r"絵の目標: ([0-9.]+)", text).group(1))' "$1/STYLE.md"
}

self_test() {
  local tmp pack clips bgm
  FINISH_NO_LOG=1
  tmp=$(mktemp -d)
  pack="$ROOT/2026-10-13/pet/01-gray-blink"
  clips="$tmp/pet-clips"
  mkdir -p "$clips" "$ROOT/samples"
  ffmpeg -y -nostdin -loglevel error -f lavfi -i "color=c=0x1c1c1c:s=1080x1920:r=30:d=5" \
    -f lavfi -i "anullsrc=r=48000:cl=stereo" -t 5 -shortest \
    -c:v libx264 -pix_fmt yuv420p -c:a aac "$clips/shot-01.mp4"
  bgm="$tmp/placeholder-bgm.wav"
  ffmpeg -y -nostdin -loglevel error -f lavfi -i "sine=frequency=220:duration=4,tremolo=f=4:d=0.6,volume=0.4" "$bgm"
  if [[ ! -f "$pack/voice/narration.wav" ]]; then
    echo "声がまだ無い: $pack/voice/narration.wav" >&2
    exit 1
  fi
  finish_one "$pack" "$clips" "" "$tmp/pet-out" "$bgm"
  local stem="2026-10-13-pet-01-gray-blink"
  local pet_target
  pet_target=$(style_target "$pack")
  assert_frame "$tmp/pet-out/${stem}.mp4" "$pet_target"
  assert_frame "$tmp/pet-out/${stem}-nobgm.mp4" "$pet_target"
  cp "$tmp/pet-out/${stem}.mp4" "$ROOT/samples/${stem}-placeholder.mp4"
  cp "$tmp/pet-out/${stem}-nobgm.mp4" "$ROOT/samples/${stem}-placeholder-nobgm.mp4"
  cp "$tmp/pet-out/${stem}-log.json" "$ROOT/samples/${stem}-placeholder-log.json"

  local kpack="$ROOT/2026-10-12/konkatsu/01-profile"
  local kclips="$tmp/kon-clips"
  mkdir -p "$kclips"
  ffmpeg -y -nostdin -loglevel error -f lavfi -i "color=c=0x202020:s=720x1280:r=30:d=6" -t 6 -an -c:v libx264 -pix_fmt yuv420p "$kclips/shot-01.mp4"
  ffmpeg -y -nostdin -loglevel error -f lavfi -i "color=c=0x303030:s=1080x1920:r=30:d=4" -t 4 -an -c:v libx264 -pix_fmt yuv420p "$kclips/shot-02.mp4"
  ffmpeg -y -nostdin -loglevel error -f lavfi -i "color=c=0x404040:s=1080x1920:r=30:d=4" -t 4 -an -c:v libx264 -pix_fmt yuv420p "$kclips/shot-03.mp4"
  finish_one "$kpack" "$kclips" "" "$tmp/kon-out" "$bgm"
  local kon_target
  kon_target=$(style_target "$kpack")
  assert_frame "$tmp/kon-out/2026-10-12-konkatsu-01-profile.mp4" "$kon_target"
  assert_frame "$tmp/kon-out/2026-10-12-konkatsu-01-profile-nobgm.mp4" "$kon_target"
  local multi_sec
  multi_sec=$(probe_duration "$tmp/kon-out/2026-10-12-konkatsu-01-profile.mp4")

  local silent_pack="$ROOT/2026-10-12/pet/01-gray-sofa-rug"
  local sclips="$tmp/silent-clips"
  mkdir -p "$sclips"
  ffmpeg -y -nostdin -loglevel error -f lavfi -i "color=c=0x111111:s=1080x1920:r=30:d=2" -t 2 -an -c:v libx264 -pix_fmt yuv420p "$sclips/shot-01.mp4"
  ffmpeg -y -nostdin -loglevel error -f lavfi -i "color=c=0x222222:s=1080x1920:r=30:d=5" -t 5 -an -c:v libx264 -pix_fmt yuv420p "$sclips/shot-02.mp4"
  ffmpeg -y -nostdin -loglevel error -f lavfi -i "color=c=0x333333:s=1080x1920:r=30:d=5" -t 5 -an -c:v libx264 -pix_fmt yuv420p "$sclips/shot-03.mp4"
  finish_one "$silent_pack" "$sclips" "" "$tmp/silent-out" ""
  local silent_target
  silent_target=$(style_target "$silent_pack")
  assert_frame "$tmp/silent-out/2026-10-12-pet-01-gray-sofa-rug-nobgm.mp4" "$silent_target"
  local silent_sec
  silent_sec=$(probe_duration "$tmp/silent-out/2026-10-12-pet-01-gray-sofa-rug-nobgm.mp4")
  if [[ -f "$tmp/silent-out/2026-10-12-pet-01-gray-sofa-rug.mp4" ]]; then
    echo "ナレーション無しの本に BGM 無し指定なのに BGM 版がある" >&2
    exit 1
  fi

  local long="$tmp/long.wav"
  ffmpeg -y -nostdin -loglevel error -i "$pack/voice/narration.wav" -filter_complex "[0:a][0:a][0:a][0:a][0:a][0:a]concat=n=6:v=0:a=1" "$long"
  local long_sec
  long_sec=$(probe_duration "$long")
  python3 -c 'import sys; raise SystemExit(0 if float(sys.argv[1])>8 else "長い声が足りない")' "$long_sec"
  finish_one "$pack" "$clips" "$long" "$tmp/long-out" ""
  assert_frame "$tmp/long-out/${stem}-nobgm.mp4" "$pet_target"

  local sine="$tmp/sine.wav" quiet="$tmp/quiet.wav"
  ffmpeg -y -nostdin -loglevel error -f lavfi -i "sine=frequency=440:sample_rate=48000:duration=1" "$sine"
  ffmpeg -y -nostdin -loglevel error -i "$sine" -af volume=0.15 "$quiet"
  python3 - "$sine" "$quiet" <<'PY'
import math, subprocess, sys

def rms_db(path):
    text = subprocess.check_output([
        "ffmpeg", "-i", path, "-af", "astats=metadata=1:reset=0", "-f", "null", "-"
    ], stderr=subprocess.STDOUT, text=True)
    for line in text.splitlines():
        if "RMS level dB" in line:
            return float(line.split(":")[-1].strip())
    raise SystemExit("RMS が測れない")

full, quiet = rms_db(sys.argv[1]), rms_db(sys.argv[2])
delta = full - quiet
expect = -20 * math.log10(0.15)
if abs(delta - expect) > 1.0:
    raise SystemExit(f"BGM 振幅が 0.15 ではない: 差 {delta:.2f} dB、期待 {expect:.2f} dB")
print(f"ok bgm delta={delta:.2f}dB expect={expect:.2f}dB")
PY

  python3 - "$ROOT/samples/${stem}-placeholder-log.json" "$tmp/long-out/${stem}-log.json" "$multi_sec" "$long_sec" "$silent_sec" <<'PY'
import json, sys
from pathlib import Path
sample = json.loads(Path(sys.argv[1]).read_text())
stretched = json.loads(Path(sys.argv[2]).read_text())
rate = stretched["fit"]["atempo"]
if rate <= 1.0:
    raise SystemExit(f"長い声なのに倍速していない: {rate}")
if abs(stretched["picture_sec"] - float(sample["picture_sec"])) > 0.05:
    raise SystemExit("絵が声に合わせて変わった")
report = {
    "sample": "samples/2026-10-13-pet-01-gray-blink-placeholder.mp4",
    "sample_nobgm": "samples/2026-10-13-pet-01-gray-blink-placeholder-nobgm.mp4",
    "sample_picture_sec": sample["picture_sec"],
    "sample_voice_sec": sample["voice_sec"],
    "sample_fit": sample["fit"],
    "sample_note": "色だけの試験映像。投稿しない。",
    "multishot_pack": "2026-10-12/konkatsu/01-profile",
    "multishot_picture_sec": float(sys.argv[3]),
    "multishot_note": "shot-01 のファイルは 6 秒。台本は 2+4+4 秒。スタイルの L 帯まで最後のフレームを足す。",
    "silent_pack": "2026-10-12/pet/01-gray-sofa-rug",
    "silent_picture_sec": float(sys.argv[5]),
    "long_voice_sec": float(sys.argv[4]),
    "long_voice_atempo": rate,
    "long_voice_picture_sec": stretched["picture_sec"],
    "captions": False,
    "frame": "1080x1920",
    "bgm_amplitude": 0.15,
    "post": False,
}
Path(sys.argv[1]).with_name("self-test.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(f"ok stretch atempo={rate:.3f} picture={stretched['picture_sec']}")
print("self-test ok")
PY
  rm -rf "$tmp"
}

if [[ "$SELF_TEST" == "1" ]]; then
  self_test
  exit 0
fi

if [[ -z "$PACK" ]]; then
  usage
  exit 2
fi

finish_one "$PACK" "$CLIPS" "$VOICE_FILE" "$OUT" "$BGM"
