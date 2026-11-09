#!/usr/bin/env bash
# 動画の機械チェック（video-done-checklist.md の「機械」行）
# 使い方: check_video.sh <ファイル.mp4> <ライン名>
#   ライン名: pet | konkatsu | beauty | kane | yua | h3
# 出力: 各行 "ID PASS/FAIL 根拠"。FAILが1つでもあれば最後に止める行を出し、終了コード1。
set -u
f="${1:-}"; line="${2:-}"
if [[ -z "$f" || -z "$line" ]]; then echo "使い方: $0 <ファイル> <pet|konkatsu|beauty|kane|yua|h3>"; exit 2; fi
if [[ ! -f "$f" ]]; then echo "ファイルが無い: $f"; exit 2; fi

# ライン別の規格: 幅 高さ fps(候補を|区切り) 最短秒 最長秒 映像コーデック(候補)
case "$line" in
  pet)      W=1080; H=1920; FPS="24|30"; DMIN=8;  DMAX=50; VC="h264" ;;
  konkatsu) W=1080; H=1920; FPS="24|30"; DMIN=8;  DMAX=60; VC="h264" ;;
  beauty)   W=1080; H=1920; FPS="24|30"; DMIN=8;  DMAX=60; VC="h264" ;;
  kane)     W=1080; H=1920; FPS="24|30"; DMIN=12; DMAX=60; VC="h264" ;;
  yua)      W=2160; H=3840; FPS="60";  DMIN=5;  DMAX=60; VC="h264|hevc" ;;
  h3)       W=1344; H=768;  FPS="24";  DMIN=60; DMAX=80; VC="h264" ;;
  *) echo "ライン名が不明: $line"; exit 2 ;;
esac

fails=(); n=0
out(){ n=$((n+1)); printf '%-4s %-4s %s\n' "$1" "$2" "$3"; if [[ "$2" == FAIL ]]; then fails+=("$1"); fi; return 0; }

probe(){ ffprobe -v error "$@" -of default=nw=1:nk=1 "$f" 2>/dev/null | head -1; }
fmt=$(probe -show_entries format=format_name)
dur=$(probe -show_entries format=duration)
vcodec=$(probe -select_streams v:0 -show_entries stream=codec_name)
w=$(probe -select_streams v:0 -show_entries stream=width)
h=$(probe -select_streams v:0 -show_entries stream=height)
rfr=$(probe -select_streams v:0 -show_entries stream=avg_frame_rate)
pix=$(probe -select_streams v:0 -show_entries stream=pix_fmt)
acodec=$(probe -select_streams a:0 -show_entries stream=codec_name)
fps=$(awk -F/ '{ if ($2>0) printf "%.2f", $1/$2; else print 0 }' <<<"${rfr:-0/1}")

# M1 コンテナ
[[ "$fmt" == *mp4* ]] && out M1 PASS "コンテナ=$fmt（mp4系）" || out M1 FAIL "コンテナ=$fmt（mp4ではない）"
# M2 映像コーデック
[[ "$vcodec" =~ ^($VC)$ ]] && out M2 PASS "映像コーデック=$vcodec（許可: $VC）" || out M2 FAIL "映像コーデック=${vcodec:-なし}（許可: $VC）"
# M3 解像度
[[ "$w" == "$W" && "$h" == "$H" ]] && out M3 PASS "解像度=${w}x${h}" || out M3 FAIL "解像度=${w}x${h}（規格 ${W}x${H}）"
# M4 fps（±0.05）
ok=0; for c in ${FPS//|/ }; do awk -v a="$fps" -v b="$c" 'BEGIN{exit !((a-b)<0.05 && (b-a)<0.05)}' && ok=1; done
[[ $ok == 1 ]] && out M4 PASS "fps=$fps" || out M4 FAIL "fps=$fps（規格 $FPS）"
# M5 長さ
awk -v d="${dur:-0}" -v a="$DMIN" -v b="$DMAX" 'BEGIN{exit !(d>=a && d<=b)}' \
  && out M5 PASS "長さ=${dur}秒（${DMIN}〜${DMAX}秒）" || out M5 FAIL "長さ=${dur}秒（規格 ${DMIN}〜${DMAX}秒）"
# M6 音声トラック
[[ "$acodec" == "aac" ]] && out M6 PASS "音声=aac" || out M6 FAIL "音声=${acodec:-なし}（aac必須）"
# M7 画素形式（スマホ再生互換）
[[ "$pix" == "yuv420p" ]] && out M7 PASS "pix_fmt=$pix" || out M7 FAIL "pix_fmt=${pix}（yuv420p必須）"
# M8 音が無音でない（平均音量 > -45dB）
if [[ -n "$acodec" ]]; then
  mv=$(ffmpeg -nostats -hide_banner -i "$f" -vn -af volumedetect -f null - 2>&1 | sed -n 's/.*mean_volume: \(-\?[0-9.]*\) dB.*/\1/p' | tail -1)
  awk -v m="${mv:--99}" 'BEGIN{exit !(m>-45)}' && out M8 PASS "平均音量=${mv}dB" || out M8 FAIL "平均音量=${mv:-測れず}dB（-45dB以下＝ほぼ無音）"
else out M8 FAIL "音声トラックが無いので測れない"; fi
# M9 冒頭1秒が真っ黒でない（フックの画がある）
bl=$(ffmpeg -nostats -hide_banner -t 1 -i "$f" -vf blackdetect=d=0.5:pic_th=0.98 -an -f null - 2>&1 | grep -c black_start)
[[ "$bl" == 0 ]] && out M9 PASS "冒頭1秒に0.5秒以上の黒画面なし" || out M9 FAIL "冒頭1秒に黒画面あり（フックの画が無い）"
# M10 縦横の向き
if [[ "$line" == h3 ]]; then
  [[ "${w:-0}" -gt "${h:-0}" ]] && out M10 PASS "横長（16:9系）" || out M10 FAIL "横長ではない"
else
  [[ "${h:-0}" -gt "${w:-0}" ]] && out M10 PASS "縦長（9:16）" || out M10 FAIL "縦長ではない"
fi

echo "---"
echo "ファイル: $f / ライン: $line / 機械チェック ${n}行"
if (( ${#fails[@]} )); then
  echo "結果: FAIL ${#fails[@]}行（${fails[*]}）→ 止める。上のFAIL行を報告して直す。"
  exit 1
fi
echo "結果: 機械チェックは全行PASS。続けて checklist の手で見る行を確認する。"
