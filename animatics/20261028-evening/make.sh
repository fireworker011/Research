#!/usr/bin/env bash
# 下書き動画（灰色の静止カード＋SRT焼き込み）。音は入れない。絵は描かない。生成AIは使わない。
# 入力は作業フォルダの外。既定は /tmp/inputs（common/ と video/）。このスクリプトは入力をコミットしない。
# 使い方: INPUTS=/tmp/inputs bash animatics/20261028-evening/make.sh
#
# カードの秒は台本のカットどおり。SRTの文言と位置タグは変えない。
# ffmpeg が SRT を ASS にすると PlayRes が 384x288 になり、9:16 では字が縦に伸びる。
# 直すのは PlayRes と字体だけ（1080x1920、文泉驛微米黑、画面上で約40px）。位置タグはそのまま。
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
INPUTS=${INPUTS:-/tmp/inputs}
BUILD=${BUILD:-/tmp/animatic-build-20261028-evening}
FONT=/usr/share/fonts/truetype/wqy/wqy-microhei.ttc
FONTDIR=/usr/share/fonts/truetype/wqy
SUBS="$INPUTS/video/subs"

if [[ ! -d "$SUBS" ]]; then
  echo "字幕フォルダが無い: $SUBS" >&2
  exit 1
fi
if [[ ! -f "$FONT" ]]; then
  echo "字体が無い: $FONT" >&2
  exit 1
fi

rm -rf "$BUILD"
mkdir -p "$BUILD"

# SRTをASSにし、画面サイズだけ合わせる。イベント行（文言・位置タグ・時刻）は触らない。
to_ass() {
  local src="$1" dst="$2"
  ffmpeg -y -hide_banner -loglevel error -i "$src" "$dst"
  sed -i \
    -e 's/^PlayResX:.*/PlayResX: 1080/' \
    -e 's/^PlayResY:.*/PlayResY: 1920/' \
    -e 's/^Style: Default,.*/Style: Default,WenQuanYi Micro Hei,40,\&H00FFFFFF,\&H000000FF,\&H00000000,\&H00000000,0,0,0,0,100,100,0,0,1,3,0,2,60,60,90,1/' \
    "$dst"
}

write_card() {
  local path="$1"
  shift
  printf '%s\n' "$@" > "$path"
}

# 引数: 名前 秒 フレーム数 最後の1秒前のフレーム番号 暗くする開始秒（空なら暗くしない）
# 続くカードは「開始秒 終了秒 テキストファイル」。終了秒が - のとき最後まで。
render() {
  local name="$1" dur="$2" frames="$3" end1="$4" dark="$5"
  shift 5
  local ass="$BUILD/${name}.ass"
  local filter="$BUILD/${name}.filter"
  local outdir="$ROOT/$name"
  mkdir -p "$outdir/frames"
  to_ass "$SUBS/${name}.srt" "$ass"
  : > "$filter"
  if [[ -n "$dark" ]]; then
    printf "drawbox=x=0:y=0:w=iw:h=ih:color=0x3A3A3A:t=fill:enable='gte(t\\,%s)',\n" "$dark" >> "$filter"
  fi
  while [[ $# -gt 0 ]]; do
    local start="$1" end="$2" textfile="$3"
    shift 3
    local enable
    if [[ "$end" == "-" ]]; then
      if [[ "$start" == "0" || "$start" == "0.0" ]]; then
        enable="gte(t\\,0)"
      else
        enable="gte(t\\,${start})"
      fi
    elif [[ "$start" == "0" || "$start" == "0.0" ]]; then
      enable="lt(t\\,${end})"
    else
      enable="gte(t\\,${start})*lt(t\\,${end})"
    fi
    cat >> "$filter" << EOF
drawtext=fontfile=${FONT}:textfile=${textfile}:fontsize=36:fontcolor=0xF5D76E:borderw=2:bordercolor=0x222222:x=(w-text_w)/2:y=430:line_spacing=8:enable='${enable}',
EOF
  done
  printf 'subtitles=%s:fontsdir=%s\n' "$ass" "$FONTDIR" >> "$filter"
  ffmpeg -y -hide_banner -loglevel error \
    -f lavfi -i "color=c=0x6A6A6A:s=1080x1920:r=24:d=${dur}" \
    -filter_script:v "$filter" \
    -frames:v "$frames" \
    -c:v libx264 -pix_fmt yuv420p -r 24 -fps_mode cfr -an \
    -movflags +faststart \
    "$outdir/draft.mp4"
  extract "$outdir/draft.mp4" 0 "$outdir/frames/0.0.png"
  extract "$outdir/draft.mp4" 12 "$outdir/frames/0.5.png"
  extract "$outdir/draft.mp4" "$end1" "$outdir/frames/end-1.png"
  echo "---- $name ----"
  ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,avg_frame_rate,pix_fmt,nb_frames \
    -select_streams v:0 -of default=nw=1 "$outdir/draft.mp4"
  local audio
  audio=$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$outdir/draft.mp4" || true)
  if [[ -z "$audio" ]]; then
    echo "音声トラック=なし"
  else
    echo "音声トラック=$audio"
  fi
}

extract() {
  local src="$1" n="$2" dst="$3"
  ffmpeg -y -hide_banner -loglevel error -i "$src" \
    -vf "select=eq(n\\,${n})" -frames:v 1 -update 1 "$dst"
}

# ペット 日だまり（台本: カット1 0.0-3.0 / 2 3.0-7.0 / 3 7.0-11.0 / 4 11.0-15.0、尺15.0秒）
write_card "$BUILD/hidamari-1.txt" \
  "カット1　0.0-3.0秒" \
  "窓辺の床の日だまり" \
  "黒猫が香箱座りで目を細めている" \
  "人は映っていない"
write_card "$BUILD/hidamari-2.txt" \
  "カット2　3.0-7.0秒" \
  "同じ画角" \
  "黒猫の右耳だけがカメラの方へ向く" \
  "体は動かない"
write_card "$BUILD/hidamari-3.txt" \
  "カット3　7.0-11.0秒" \
  "同じ画角" \
  "目を半分あけてレンズを見て" \
  "ゆっくり閉じる"
write_card "$BUILD/hidamari-4.txt" \
  "カット4　11.0-15.0秒" \
  "同じ画角" \
  "目を閉じたまま" \
  "日だまりの中で動かない"
render "2026-10-28-ペット-kuroneko-hidamari" 15 360 336 "" \
  0 3 "$BUILD/hidamari-1.txt" \
  3 7 "$BUILD/hidamari-2.txt" \
  7 11 "$BUILD/hidamari-3.txt" \
  11 - "$BUILD/hidamari-4.txt"

# ペット 天板（台本: 0.0-3.0 / 3.0-6.5 / 6.5-10.0 / 10.0-15.0、尺15.0秒）
write_card "$BUILD/tower-1.txt" \
  "カット1　0.0-3.0秒" \
  "猫タワーの天板" \
  "黒猫が香箱座りで止まっている" \
  "人は映っていない"
write_card "$BUILD/tower-2.txt" \
  "カット2　3.0-6.5秒" \
  "同じ画角" \
  "しっぽの先だけが1回動いて止まる"
write_card "$BUILD/tower-3.txt" \
  "カット3　6.5-10.0秒" \
  "同じ画角" \
  "顔を少し下へ向け" \
  "目を半分あけて、また細める"
write_card "$BUILD/tower-4.txt" \
  "カット4　10.0-15.0秒" \
  "同じ画角" \
  "目を細めたまま天板で動かない"
render "2026-10-29-ペット-kuroneko-tower" 15 360 336 "" \
  0 3 "$BUILD/tower-1.txt" \
  3 6.5 "$BUILD/tower-2.txt" \
  6.5 10 "$BUILD/tower-3.txt" \
  10 - "$BUILD/tower-4.txt"

# 金メモ 保険のハガキ（台本: 0.0-3.0 / 3.0-6.5 / 6.5-10.0 / 10.0-13.0、尺13.0秒）
write_card "$BUILD/hagaki-1.txt" \
  "カット1　0.0-3.0秒" \
  "ゴミ箱の真上でハガキを1枚つまむ" \
  "目を丸くして止まる30代の会社員"
write_card "$BUILD/hagaki-2.txt" \
  "カット2　3.0-6.5秒" \
  "ハガキを顔の前に持ち上げてのぞきこむ" \
  "編集の札「控除証明書」"
write_card "$BUILD/hagaki-3.txt" \
  "カット3　6.5-10.0秒" \
  "机の書類にハガキを重ね" \
  "クリップで1回とめる" \
  "編集の札「年末調整の紙」"
write_card "$BUILD/hagaki-4.txt" \
  "カット4　10.0-13.0秒" \
  "書類をクリアファイルに入れる" \
  "胸に抱えて1回うなずく"
render "2026-10-28-金メモ-hoken-hagaki" 13 312 288 "" \
  0 3 "$BUILD/hagaki-1.txt" \
  3 6.5 "$BUILD/hagaki-2.txt" \
  6.5 10 "$BUILD/hagaki-3.txt" \
  10 - "$BUILD/hagaki-4.txt"

# 婚活 高そう（台本: 0.0-3.0 / 3.0-6.0 / 6.0-13.0、13.0-15.0はカット3を少し暗くする。尺15.0秒）
write_card "$BUILD/takasou-1.txt" \
  "カット1　0.0-3.0秒" \
  "昼の机。ノートPCが1台" \
  "明るい画面。人物なし" \
  "札「相談所のサイト」"
write_card "$BUILD/takasou-2.txt" \
  "カット2　3.0-6.0秒" \
  "同じPCの画面に寄る" \
  "下の四角に数字はない" \
  "札「入会の案内」"
write_card "$BUILD/takasou-3.txt" \
  "カット3　6.0-13.0秒" \
  "PCは奥で閉じている" \
  "手前は資料の束が1つ" \
  "札「いくつかの相談所の資料」"
write_card "$BUILD/takasou-4.txt" \
  "カット3のまま　13.0-15.0秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上のPRは残す"
render "2026-11-01-婚活-takasou" 15 360 336 13 \
  0 3 "$BUILD/takasou-1.txt" \
  3 6 "$BUILD/takasou-2.txt" \
  6 13 "$BUILD/takasou-3.txt" \
  13 - "$BUILD/takasou-4.txt"

# 婚活 日曜（台本: 0.0-3.0 / 3.0-6.4 / 6.4-13.0、13.0-15.0はカット3を少し暗くする。尺15.0秒）
# 6.4秒は24fpsで153.6フレームになり割り切れない。境目は t<6.4 と t>=6.4（フレーム153と154の間）。
write_card "$BUILD/nichiyou-1.txt" \
  "カット1　0.0-3.0秒" \
  "白い壁の真っ白なホワイトボード" \
  "札「日曜の予定」" \
  "人は映っていない"
write_card "$BUILD/nichiyou-2.txt" \
  "カット2　3.0-6.4秒" \
  "ローテーブルのタブレット" \
  "相談所パンフの見開き。文字なし" \
  "札「相談所のパンフ」"
write_card "$BUILD/nichiyou-3.txt" \
  "カット3　6.4-13.0秒" \
  "タブレットの画面に寄る" \
  "別の相談所のパンフに変わる" \
  "札「何社かの相談所の資料」"
write_card "$BUILD/nichiyou-4.txt" \
  "カット3のまま　13.0-15.0秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上のPRは残す"
render "2026-11-02-婚活-nichiyou-yotei" 15 360 336 13 \
  0 3 "$BUILD/nichiyou-1.txt" \
  3 6.4 "$BUILD/nichiyou-2.txt" \
  6.4 13 "$BUILD/nichiyou-3.txt" \
  13 - "$BUILD/nichiyou-4.txt"

echo "完了"
