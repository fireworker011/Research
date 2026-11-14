#!/usr/bin/env bash
# tools/check_video.sh の長さ判定。下書きも --final も 8.0〜10.5秒。
# 合成の単色mp4だけで見る。本編のレンダーと収録音声は作らない。
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
CHECK="$ROOT/check_video.sh"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
fail=0

if grep -E '^[[:space:]]*[^#].*abs\([^)]*10\.5' "$CHECK" >/dev/null; then
  echo "FAIL 等値判定の式が残っている" >&2
  exit 1
fi

expect_m12() {
  local raw=$1 want=$2 want_exit=$3
  local out code got
  set +e
  out=$(bash "$CHECK" --m12-fixture "$raw" 2>&1)
  code=$?
  set -e
  got=$(printf '%s\n' "$out" | awk '$1=="M12"{print $2}')
  if [[ "$got" == "$want" && "$code" == "$want_exit" ]] && ! printf '%s\n' "$out" | grep -q 'syntax error'; then
    printf 'PASS\tm12\tM12=%s\texit=%s\n' "$got" "$code"
  else
    printf 'FAIL\tm12\tgot=%s(want %s)\texit=%s(want %s)\n' "$got" "$want" "$code" "$want_exit" >&2
    printf '%s\n' "$out" >&2
    fail=1
  fi
}

expect_m12 skip SKIP 0
expect_m12 $'skip\r' SKIP 0
expect_m12 $'skip\n' SKIP 0
expect_m12 $'skip\r\n' SKIP 0
expect_m12 39 FAIL 1
expect_m12 40 PASS 0

make_mp4() {
  local frames="$1" audio="$2" out="$3"
  local dur
  dur=$(python3 -c "print(${frames}/24)")
  if [[ "$audio" == "aac" ]]; then
    ffmpeg -y -hide_banner -loglevel error \
      -f lavfi -i "color=c=0x2244aa:s=1080x1920:r=24:d=${dur}" \
      -f lavfi -i "sine=frequency=440:sample_rate=48000:duration=${dur}" \
      -frames:v "$frames" -r 24 \
      -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest \
      "$out"
  else
    ffmpeg -y -hide_banner -loglevel error \
      -f lavfi -i "color=c=0x2244aa:s=1080x1920:r=24:d=${dur}" \
      -frames:v "$frames" -r 24 \
      -c:v libx264 -pix_fmt yuv420p -an \
      "$out"
  fi
}

m5_of() {
  printf '%s\n' "$1" | awk '$1=="M5"{print $2}'
}

field_of() {
  printf '%s\n' "$1" | awk -v id="$2" '$1==id{print $2}'
}

run_case() {
  local name="$1" frames="$2" audio="$3" lane="$4" mode="$5" want_m5="$6" want_exit="$7" want_m6="${8:-}" want_m8="${9:-}"
  local file="$TMP/${name}.mp4"
  make_mp4 "$frames" "$audio" "$file"
  local probe
  probe=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$file")
  local args=("$CHECK" "$file" "$lane")
  if [[ "$mode" == "final" ]]; then
    args+=("--final")
  fi
  local out code
  set +e
  out=$("${args[@]}" 2>&1)
  code=$?
  set -e
  local got got_m6 got_m8 got_m12
  got=$(m5_of "$out")
  got_m6=$(field_of "$out" M6)
  got_m8=$(field_of "$out" M8)
  got_m12=$(field_of "$out" M12)
  local ids_ok=1
  local id
  for id in M1 M2 M3 M4 M5 M6 M7 M8 M9 M10 M11 M12 M13 M14; do
    if ! printf '%s\n' "$out" | awk -v id="$id" '$1==id{found=1} END{exit !found}'; then
      ids_ok=0
    fi
  done
  local audio_ok=1
  if [[ -n "$want_m6" && "$got_m6" != "$want_m6" ]]; then
    audio_ok=0
  fi
  if [[ -n "$want_m8" && "$got_m8" != "$want_m8" ]]; then
    audio_ok=0
  fi
  local m12_ok=1
  if [[ "$got_m12" != "SKIP" ]] || printf '%s\n' "$out" | grep -q 'syntax error'; then
    m12_ok=0
  fi
  if [[ "$got" == "$want_m5" && "$code" == "$want_exit" && "$ids_ok" == "1" && "$audio_ok" == "1" && "$m12_ok" == "1" ]]; then
    printf 'PASS\t%s\tprobe=%s\tM5=%s\tM6=%s\tM8=%s\tM12=%s\texit=%s\n' "$name" "$probe" "$got" "$got_m6" "$got_m8" "$got_m12" "$code"
  else
    printf 'FAIL\t%s\tprobe=%s\tM5=%s(want %s)\tM6=%s(want %s)\tM8=%s(want %s)\tM12=%s(want SKIP)\texit=%s(want %s)\tids=%s\n' \
      "$name" "$probe" "$got" "$want_m5" "$got_m6" "${want_m6:-any}" "$got_m8" "${want_m8:-any}" "$got_m12" "$code" "$want_exit" "$ids_ok" >&2
    printf '%s\n' "$out" >&2
    fail=1
  fi
  if [[ "$mode" == "final" && "$got" == "PASS" ]]; then
    if ! printf '%s\n' "$out" | grep -q '8.0〜10.5秒（完成）'; then
      echo "FAIL ${name} の合格表示が完成の範囲ではない" >&2
      fail=1
    fi
  fi
}

# 9.0秒は新しい範囲の内。古い 10.500±0.050 では不合格。
run_case final-pet-9.0 216 aac pet final PASS 0 PASS PASS
run_case final-kane-9.0 216 aac kane final PASS 0 PASS PASS
# 端。8.0 と 10.5 は含む。
run_case final-pet-8.0 192 aac pet final PASS 0 PASS PASS
run_case final-kane-10.5 252 aac kane final PASS 0 PASS PASS
# 10.541667秒は 10.500±0.050 の内。新しい範囲の外。
run_case final-pet-10.54 253 aac pet final FAIL 1 PASS PASS
run_case final-kane-11.0 264 aac kane final FAIL 1 PASS PASS
run_case final-pet-7.96 191 aac pet final FAIL 1 PASS PASS
# 下書きは同じ長さ。音声が無くても M6 と M8 は不合格にしない。
run_case draft-pet-9.0 216 none pet draft PASS 0 PASS PASS
run_case draft-kane-11.0 264 none kane draft FAIL 1 PASS PASS
# 完成で音声が無いと、長さが範囲内でも M6 と M8 で止まる。
run_case final-silent-9.0 216 none pet final PASS 1 FAIL FAIL

if [[ "$fail" != "0" ]]; then
  exit 1
fi
echo "ALL PASS"
