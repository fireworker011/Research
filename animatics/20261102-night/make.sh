#!/usr/bin/env bash
# 下書き動画（灰色の静止カード＋SRT焼き込み＋女性AIのナレーション）。絵は描かない。
# 字幕は同じフォルダの subs/。台本ファイルはコミットしない。
# 2026-11-04: 尺は10.5秒。秒は0.5刻み。ペットの右上の記号は出さない。
# 音なしは取り消した。narrate.py が字幕の台詞を aac で読む。
# 使い方: bash animatics/20261102-night/make.sh
# 1本だけ: ONLY=<名前> bash animatics/20261102-night/make.sh
#
# カードの秒は10.5秒のカットどおり。字幕の時刻は0.5刻み。
# ffmpeg が SRT を ASS にすると PlayRes が 384x288 になり、9:16 では字が縦に伸びる。
# 直すのは PlayRes と字体だけ（1080x1920、文泉驛微米黑、画面上で約40px）。
# 金メモの台詞行には位置タグが無い。焼き込み時だけ下（{\an2}）にする。文言と時刻はそのまま。
# 早見表・右の金額・出典・クレジットは、台本の画面文字を編集の文字として載せる。SRTには入れない。
# いらすとやの画像は使っていないので、「イラスト：いらすとや」は載せない。
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
BUILD=${BUILD:-/tmp/animatic-build-20261102-night}
FONT=/usr/share/fonts/truetype/wqy/wqy-microhei.ttc
FONTDIR=/usr/share/fonts/truetype/wqy
SUBS="$ROOT/subs"

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

# SRTをASSにし、画面サイズだけ合わせる。位置タグと文言はここでは変えない。
to_ass() {
  local src="$1" dst="$2"
  ffmpeg -y -hide_banner -loglevel error -i "$src" "$dst"
  sed -i \
    -e 's/^PlayResX:.*/PlayResX: 1080/' \
    -e 's/^PlayResY:.*/PlayResY: 1920/' \
    -e 's/^Style: Default,.*/Style: Default,WenQuanYi Micro Hei,40,\&H00FFFFFF,\&H000000FF,\&H00000000,\&H00000000,0,0,0,0,100,100,0,0,1,3,0,2,60,60,90,1/' \
    "$dst"
}

# 金メモだけ。位置タグが無い台詞を下に置く。フックの {\an8} はそのまま。文言と時刻は変えない。
place_kane() {
  local ass="$1"
  python3 - "$ass" << 'PY'
import sys
path = sys.argv[1]
lines = open(path, encoding="utf-8").read().splitlines(True)
out = []
for line in lines:
    if not line.startswith("Dialogue:"):
        out.append(line)
        continue
    parts = line.rstrip("\n").split(",", 9)
    if len(parts) < 10:
        out.append(line if line.endswith("\n") else line + "\n")
        continue
    body = parts[9]
    if "{\\an8}" in body:
        parts[7] = "70"
    elif "{\\an" not in body:
        parts[7] = "220"
        parts[9] = "{\\an2}" + body
    out.append(",".join(parts) + "\n")
open(path, "w", encoding="utf-8").writelines(out)
PY
}

write_card() {
  local path="$1"
  shift
  printf '%s\n' "$@" > "$path"
}

# textfile size color x y enable を、オーバーレイファイルへ足す。
add_text() {
  local overlay="$1" textfile="$2" size="$3" color="$4" x="$5" y="$6" enable="$7"
  printf "drawtext=fontfile=%s:textfile=%s:expansion=none:fontsize=%s:fontcolor=%s:borderw=2:bordercolor=0x222222:x=%s:y=%s:line_spacing=8:enable='%s',\n" \
    "$FONT" "$textfile" "$size" "$color" "$x" "$y" "$enable" >> "$overlay"
}

# 引数: 名前 秒 フレーム数 最後の1秒前のフレーム番号 暗くする開始秒（空なら暗くしない）
# 続くカードは「開始秒 終了秒 テキストファイル」。終了秒が - のとき最後まで。
render() {
  local name="$1" dur="$2" frames="$3" end1="$4" dark="$5"
  shift 5
  if [[ -n "${ONLY:-}" && "$name" != "$ONLY" ]]; then
    return 0
  fi
  local ass="$BUILD/${name}.ass"
  local filter="$BUILD/${name}.filter"
  local outdir="$ROOT/$name"
  if [[ ! -f "$SUBS/${name}.srt" ]]; then
    echo "SRTなし: $name" >&2
    exit 1
  fi
  mkdir -p "$outdir/frames"
  to_ass "$SUBS/${name}.srt" "$ass"
  if [[ "$name" == *金メモ* ]]; then
    place_kane "$ass"
  fi
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
drawtext=fontfile=${FONT}:textfile=${textfile}:expansion=none:fontsize=36:fontcolor=0xF5D76E:borderw=2:bordercolor=0x222222:x=(w-text_w)/2:y=430:line_spacing=8:enable='${enable}',
EOF
  done
  if [[ -f "$BUILD/${name}.overlay" ]]; then
    cat "$BUILD/${name}.overlay" >> "$filter"
  fi
  printf 'subtitles=%s:fontsdir=%s\n' "$ass" "$FONTDIR" >> "$filter"
  python3 "$ROOT/narrate.py" "$SUBS/${name}.srt" "$BUILD/${name}.m4a" "$dur"
  ffmpeg -y -hide_banner -loglevel error \
    -f lavfi -i "color=c=0x6A6A6A:s=1080x1920:r=24:d=${dur}" \
    -i "$BUILD/${name}.m4a" \
    -filter_script:v "$filter" \
    -frames:v "$frames" \
    -map 0:v:0 -map 1:a:0 \
    -c:v libx264 -pix_fmt yuv420p -r 24 -fps_mode cfr \
    -c:a aac -b:a 160k -ar 48000 \
    -t "$dur" \
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

# ペット カーテン（台本: 0.0-2.0 / 2.0-4.0 / 4.0-6.5 / 6.5-8.5。8.5-10.5は少し暗くする。尺10.5秒）
write_card "$BUILD/kaaten-1.txt" \
  "カット1　0.0-2.0秒" \
  "生成りのカーテンの裾の横" \
  "黒猫が座って止まっている" \
  "まばたき1回。前足は床。人は映っていない"
write_card "$BUILD/kaaten-2.txt" \
  "カット2　2.0-4.0秒" \
  "同じ画角" \
  "しっぽの先が1回揺れて止まる" \
  "体と前足は動かない。布には触れない"
write_card "$BUILD/kaaten-3.txt" \
  "カット3　4.0-6.5秒" \
  "同じ画角。頭の位置はそのまま" \
  "視線だけが裾へ1回向く" \
  "前足は床。しっぽの先は止まっている"
write_card "$BUILD/kaaten-4.txt" \
  "カット4　6.5-8.5秒" \
  "同じ画角" \
  "腹が息で1回ふくらんで戻る" \
  "座ったまま。裾には触れない"
write_card "$BUILD/kaaten-5.txt" \
  "カット4のまま　8.5-10.5秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上の記号は出さない。人は映っていない"
render "2026-11-11-ペット-kuroneko-kaaten" 10.5 252 228 8.5 \
  0 1.75 "$BUILD/kaaten-1.txt" \
  1.75 3.75 "$BUILD/kaaten-2.txt" \
  3.75 6.625 "$BUILD/kaaten-3.txt" \
  6.625 8.5 "$BUILD/kaaten-4.txt" \
  8.5 - "$BUILD/kaaten-5.txt"

# ペット 猫草（台本: 0.0-2.0 / 2.0-4.0 / 4.0-6.0 / 6.0-8.5。8.5-10.5は少し暗くする。尺10.5秒）
write_card "$BUILD/kusa-1.txt" \
  "カット1　0.0-2.0秒" \
  "白い鉢の猫草の横" \
  "黒猫が座って止まっている" \
  "まばたき1回。顔は草の外。口は閉じている"
write_card "$BUILD/kusa-2.txt" \
  "カット2　2.0-4.0秒" \
  "同じ画角。頭の位置はそのまま" \
  "視線だけが猫草の方へ1回向く" \
  "口は閉じている。顔は草に入っていない"
write_card "$BUILD/kusa-3.txt" \
  "カット3　4.0-6.0秒" \
  "同じ画角" \
  "耳が1回、猫草の方へ向く" \
  "体と前足は動かない。草には触れない"
write_card "$BUILD/kusa-4.txt" \
  "カット4　6.0-8.5秒" \
  "同じ画角" \
  "まばたき1回のあと、目を開ける" \
  "口は閉じたまま。顔は草の外"
write_card "$BUILD/kusa-5.txt" \
  "カット4のまま　8.5-10.5秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上の記号は出さない。口は閉じている"
render "2026-11-12-ペット-kuroneko-nekokusa" 10.5 252 228 8.5 \
  0 2.375 "$BUILD/kusa-1.txt" \
  2.375 4.25 "$BUILD/kusa-2.txt" \
  4.25 6.375 "$BUILD/kusa-3.txt" \
  6.375 8.5 "$BUILD/kusa-4.txt" \
  8.5 - "$BUILD/kusa-5.txt"

# ペット ブラシ（台本: 0.0-2.5 / 2.5-4.5 / 4.5-6.5 / 6.5-8.5。8.5-10.5は少し暗くする。尺10.5秒）
write_card "$BUILD/brush-1.txt" \
  "カット1　0.0-2.5秒" \
  "ピンクのアーチの横" \
  "黒猫が座って止まっている" \
  "体はアーチの外。まばたき1回。前足は床"
write_card "$BUILD/brush-2.txt" \
  "カット2　2.5-4.5秒" \
  "同じ画角" \
  "耳が1回、アーチの方へ向く" \
  "体は外のまま。前足は動かない"
write_card "$BUILD/brush-3.txt" \
  "カット3　4.5-6.5秒" \
  "同じ画角" \
  "目を少し細める" \
  "体は起きたまま。アーチに入らない"
write_card "$BUILD/brush-4.txt" \
  "カット4　6.5-8.5秒" \
  "同じ画角" \
  "腹が息で1回ふくらんで戻る" \
  "座ったまま。こすらない。前足は床"
write_card "$BUILD/brush-5.txt" \
  "カット4のまま　8.5-10.5秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上の記号は出さない。前足は隠さない"
render "2026-11-13-ペット-kuroneko-burashi" 10.5 252 228 8.5 \
  0 2.125 "$BUILD/brush-1.txt" \
  2.125 4 "$BUILD/brush-2.txt" \
  4 6.25 "$BUILD/brush-3.txt" \
  6.25 8.5 "$BUILD/brush-4.txt" \
  8.5 - "$BUILD/brush-5.txt"

# 金メモ 障害年金（台本: 0.0-3.0 / 3.0-8.5 / 8.5-10.5。PRなし。尺10.5秒）
# 右の金額は 0.0-3.0。1級の行は 0.5、2級の行は 3.0、3級の行は 5.5。
# 635,500円は 5.5 まで出さない。8.5 で見出しの生年月日を明るくする。円は台本の表のまま。
NAME="2026-11-09-金メモ-shogai-nenkin"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/sho-right-big.txt" "1級 → 1,059,125円"
write_card "$BUILD/sho-right-small.txt" "昭和31年4月2日以後・年額"
write_card "$BUILD/sho-head.txt" "日本年金機構・令和8年4月分から"
write_card "$BUILD/sho-born.txt" "昭和31年4月2日以後生まれ"
write_card "$BUILD/sho-row1.txt" \
  "障害基礎年金・1級" \
  "1,059,125円"
write_card "$BUILD/sho-row2.txt" \
  "障害基礎年金・2級" \
  "847,300円"
write_card "$BUILD/sho-row3.txt" \
  "障害厚生年金・3級の最低保障額" \
  "635,500円"
write_card "$BUILD/sho-foot.txt" \
  "令和8年4月分から" \
  "納付要件あり" \
  "子の加算・配偶者の加給" \
  "報酬比例の円は、この表に無い"
write_card "$BUILD/sho-src.txt" "出典：日本年金機構"
write_card "$BUILD/sho-credit.txt" "声：女性AI"
add_text "$OV" "$BUILD/sho-right-big.txt" 40 white "w-text_w-80" 860 'lt(t\,3)'
add_text "$OV" "$BUILD/sho-right-small.txt" 26 white "w-text_w-80" 916 'lt(t\,3)'
add_text "$OV" "$BUILD/sho-head.txt" 28 white 40 660 'gte(t\,0.5)'
add_text "$OV" "$BUILD/sho-born.txt" 28 0xBDBDBD 40 708 'gte(t\,0.0)*lt(t\,8.125)'
add_text "$OV" "$BUILD/sho-born.txt" 28 white 40 708 'gte(t\,8.125)'
add_text "$OV" "$BUILD/sho-row1.txt" 28 white 40 780 'gte(t\,0.0)*lt(t\,2.75)'
add_text "$OV" "$BUILD/sho-row1.txt" 28 0xBDBDBD 40 780 'gte(t\,2.75)'
add_text "$OV" "$BUILD/sho-row2.txt" 28 white 40 900 'gte(t\,2.75)*lt(t\,5.375)'
add_text "$OV" "$BUILD/sho-row2.txt" 28 0xBDBDBD 40 900 'gte(t\,5.375)'
add_text "$OV" "$BUILD/sho-row3.txt" 28 white 40 1020 'gte(t\,5.375)*lt(t\,8.125)'
add_text "$OV" "$BUILD/sho-row3.txt" 28 0xBDBDBD 40 1020 'gte(t\,8.125)'
add_text "$OV" "$BUILD/sho-foot.txt" 24 0xE6E6E6 40 1180 'gte(t\,0.5)'
add_text "$OV" "$BUILD/sho-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/sho-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,0)'
write_card "$BUILD/sho-1.txt" \
  "カット1　0.0-3.0秒" \
  "文字の無い閉じた冊子を持つ成人" \
  "目を丸くして止まっている" \
  "右に1,059,125円。人物は成人だけ"
write_card "$BUILD/sho-2.txt" \
  "カット2　3.0-8.5秒" \
  "同じ成人が左下で冊子を机に置く" \
  "中央に早見表" \
  "人物は成人だけ"
write_card "$BUILD/sho-3.txt" \
  "カット3　8.5-10.5秒" \
  "同じ成人が冊子を横に置く" \
  "うなずく。指はささない" \
  "表は上に残す。人物は成人だけ"
render "$NAME" 10.5 252 228 "" \
  0 3 "$BUILD/sho-1.txt" \
  3 8.5 "$BUILD/sho-2.txt" \
  8.5 - "$BUILD/sho-3.txt"

# 金メモ 再就職手当（台本: 0.0-3.0 / 3.0-8.5 / 8.5-10.5。PRなし。尺10.5秒）
# 行は 0.5、3.0、5.5、8.5。638,400円は 3.0 まで、427,200円は 5.5 まで、6,745円は 8.5 まで出さない。
# 円は台本の表のまま。6,745円に日数を掛けた円は出さない。
NAME="2026-11-10-金メモ-saishushoku-teate"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/sai-right-big.txt" "残90日 → 252,000円"
write_card "$BUILD/sai-right-small.txt" "日額4,000円の例・70%"
write_card "$BUILD/sai-head.txt" "厚生労働省PDFの例・基本手当日額4,000円"
write_card "$BUILD/sai-row90.txt" \
  "例・日額4,000円・所定90日" \
  "残90日・70%" \
  "252,000円"
write_card "$BUILD/sai-row228.txt" \
  "例・日額4,000円・所定270日" \
  "50日目に就職・残228日・70%" \
  "638,400円"
write_card "$BUILD/sai-row178.txt" \
  "例・日額4,000円・所定270日" \
  "100日目に就職・残178日・60%" \
  "427,200円"
write_card "$BUILD/sai-row-cap.txt" \
  "日額の上限・60歳未満" \
  "令和9年7月31日まで・6,745円" \
  "60歳以上65歳未満は5,454円"
write_card "$BUILD/sai-foot.txt" \
  "例。要件がある" \
  "残日数が所定給付日数の3分の2以上で70%" \
  "3分の1以上で60%" \
  "4,000円は上限ではない"
write_card "$BUILD/sai-src.txt" "出典：ハローワーク"
write_card "$BUILD/sai-credit.txt" "声：女性AI"
add_text "$OV" "$BUILD/sai-right-big.txt" 40 white "w-text_w-80" 860 'lt(t\,3)'
add_text "$OV" "$BUILD/sai-right-small.txt" 26 white "w-text_w-80" 916 'lt(t\,3)'
add_text "$OV" "$BUILD/sai-head.txt" 28 white 40 640 'gte(t\,0.5)'
add_text "$OV" "$BUILD/sai-row90.txt" 26 white 40 720 'gte(t\,0.0)*lt(t\,5.25)'
add_text "$OV" "$BUILD/sai-row90.txt" 26 0xBDBDBD 40 720 'gte(t\,5.25)'
add_text "$OV" "$BUILD/sai-row228.txt" 26 white 40 860 'lt(t\,0)'
add_text "$OV" "$BUILD/sai-row228.txt" 26 0xBDBDBD 40 860 'gte(t\,0.0)'
add_text "$OV" "$BUILD/sai-row178.txt" 26 white 40 1020 'lt(t\,0)'
add_text "$OV" "$BUILD/sai-row178.txt" 26 0xBDBDBD 40 1020 'gte(t\,0.0)'
add_text "$OV" "$BUILD/sai-row-cap.txt" 26 white 40 1180 'gte(t\,5.25)'
add_text "$OV" "$BUILD/sai-foot.txt" 22 0xE6E6E6 40 1360 'gte(t\,0.5)'
add_text "$OV" "$BUILD/sai-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/sai-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,0)'
write_card "$BUILD/sai-1.txt" \
  "カット1　0.0-3.0秒" \
  "文字の無いカバンを持つ成人" \
  "目を丸くして止まっている" \
  "右に252,000円。人物は成人だけ"
write_card "$BUILD/sai-2.txt" \
  "カット2　3.0-8.5秒" \
  "同じ成人が左下でカバンを机に置く" \
  "中央に早見表" \
  "人物は成人だけ"
write_card "$BUILD/sai-3.txt" \
  "カット3　8.5-10.5秒" \
  "同じ成人がカバンを横に置く" \
  "うなずく。指はささない" \
  "表は上に残す。人物は成人だけ"
render "$NAME" 10.5 252 228 "" \
  0 3 "$BUILD/sai-1.txt" \
  3 8.5 "$BUILD/sai-2.txt" \
  8.5 - "$BUILD/sai-3.txt"

# 金メモ 教育訓練（台本: 0.0-3.0 / 3.0-8.5 / 8.5-10.5。PRなし。尺10.5秒）
# 行は 0.5、3.0、5.5、8.5。20万円は 3.0 まで、40万円は 5.5 まで、64万円は 8.5 まで出さない。
# 56万円・25万円・192万円は画面に出さない。円は台本の表のまま。
NAME="2026-11-11-金メモ-kyoiku-kunren"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/kyo-right-big.txt" "20% → 10万円"
write_card "$BUILD/kyo-right-small.txt" "一般・上限"
write_card "$BUILD/kyo-head.txt" "ハローワーク・教育訓練経費の上限"
write_card "$BUILD/kyo-row20.txt" \
  "一般・20%" \
  "10万円"
write_card "$BUILD/kyo-row40.txt" \
  "特定一般・40%" \
  "20万円"
write_card "$BUILD/kyo-row50.txt" \
  "専門実践・50%" \
  "年間40万円"
write_card "$BUILD/kyo-row80.txt" \
  "専門実践・80%（要件あり）" \
  "年間上限64万円"
write_card "$BUILD/kyo-foot.txt" \
  "支払った教育訓練経費に対する上限" \
  "20%・40%・50%は" \
  "計算額が4千円を超えないときは出ない"
write_card "$BUILD/kyo-src.txt" "出典：ハローワーク"
write_card "$BUILD/kyo-credit.txt" "声：女性AI"
add_text "$OV" "$BUILD/kyo-right-big.txt" 42 white "w-text_w-80" 860 'lt(t\,3)'
add_text "$OV" "$BUILD/kyo-right-small.txt" 28 white "w-text_w-80" 916 'lt(t\,3)'
add_text "$OV" "$BUILD/kyo-head.txt" 28 white 40 660 'gte(t\,0.5)'
add_text "$OV" "$BUILD/kyo-row20.txt" 28 white 40 760 'gte(t\,0.0)*lt(t\,3.125)'
add_text "$OV" "$BUILD/kyo-row20.txt" 28 0xBDBDBD 40 760 'gte(t\,3.125)'
add_text "$OV" "$BUILD/kyo-row40.txt" 28 white 40 880 'gte(t\,3.125)*lt(t\,6.75)'
add_text "$OV" "$BUILD/kyo-row40.txt" 28 0xBDBDBD 40 880 'gte(t\,6.75)'
add_text "$OV" "$BUILD/kyo-row50.txt" 28 white 40 1000 'gte(t\,6.75)'
add_text "$OV" "$BUILD/kyo-row50.txt" 28 0xBDBDBD 40 1000 'lt(t\,0)'
add_text "$OV" "$BUILD/kyo-row80.txt" 28 0xBDBDBD 40 1120 'gte(t\,0.0)'
add_text "$OV" "$BUILD/kyo-foot.txt" 24 0xE6E6E6 40 1280 'gte(t\,0.5)'
add_text "$OV" "$BUILD/kyo-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/kyo-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,0)'
write_card "$BUILD/kyo-1.txt" \
  "カット1　0.0-3.0秒" \
  "文字の無いパンフレットを立てた成人" \
  "目を丸くして止まっている" \
  "右に10万円。人物は成人だけ"
write_card "$BUILD/kyo-2.txt" \
  "カット2　3.0-8.5秒" \
  "同じ成人が左下でパンフレットを伏せる" \
  "中央に早見表" \
  "人物は成人だけ"
write_card "$BUILD/kyo-3.txt" \
  "カット3　8.5-10.5秒" \
  "同じ成人がパンフレットを横に置く" \
  "うなずく。指はささない" \
  "表は上に残す。人物は成人だけ"
render "$NAME" 10.5 252 228 "" \
  0 3 "$BUILD/kyo-1.txt" \
  3 8.5 "$BUILD/kyo-2.txt" \
  8.5 - "$BUILD/kyo-3.txt"

echo "完了"
