#!/usr/bin/env bash
# 下書き動画（灰色の静止カード＋SRT焼き込み）。音は入れない。絵は描かない。生成AIは使わない。
# 字幕は同じフォルダの subs/（入力のSRTをそのまま）。台本ファイルはコミットしない。
# 使い方: bash animatics/20261031-night/make.sh
# 1本だけ: ONLY=<名前> bash animatics/20261031-night/make.sh
#
# カードの秒は台本のカットどおり。字幕の文言と時刻は変えない。
# ffmpeg が SRT を ASS にすると PlayRes が 384x288 になり、9:16 では字が縦に伸びる。
# 直すのは PlayRes と字体だけ（1080x1920、文泉驛微米黑、画面上で約40px）。
# 金メモの台詞行には位置タグが無い。焼き込み時だけ下（{\an2}）にする。文言と時刻はそのまま。
# 早見表・右の金額・出典・クレジットは、台本の画面文字を編集の文字として載せる。SRTには入れない。
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
BUILD=${BUILD:-/tmp/animatic-build-20261031-night}
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

# ペット ドア（台本: 0.0-3.6 / 3.6-7.0 / 7.0-10.2 / 10.2-15.0。13.0-15.0は少し暗くする。尺15.0秒）
write_card "$BUILD/tobira-1.txt" \
  "カット1　0.0-3.6秒" \
  "すき間の開いた木のドアの前" \
  "黒猫が座って止まっている" \
  "まばたき1回。前足は床。人は映っていない"
write_card "$BUILD/tobira-2.txt" \
  "カット2　3.6-7.0秒" \
  "同じ画角" \
  "耳が1回、ドアの方へ向く" \
  "体と前足は動かない。立たない"
write_card "$BUILD/tobira-3.txt" \
  "カット3　7.0-10.2秒" \
  "同じ画角。前足は床" \
  "目を少し細める" \
  "座ったまま。立ち上がらない"
write_card "$BUILD/tobira-4.txt" \
  "カット4　10.2-13.0秒" \
  "同じ画角" \
  "腹が息で1回ふくらんで戻る" \
  "座ったまま。すき間を通らない"
write_card "$BUILD/tobira-5.txt" \
  "カット4のまま　13.0-15.0秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上のPRは残す。人は映っていない"
render "2026-11-08-ペット-kuroneko-tobira" 15 360 336 13 \
  0 3.6 "$BUILD/tobira-1.txt" \
  3.6 7.0 "$BUILD/tobira-2.txt" \
  7.0 10.2 "$BUILD/tobira-3.txt" \
  10.2 13 "$BUILD/tobira-4.txt" \
  13 - "$BUILD/tobira-5.txt"

# ペット ボール（台本: 0.0-3.6 / 3.6-7.0 / 7.0-10.2 / 10.2-15.0。13.0-15.0は少し暗くする。尺15.0秒）
write_card "$BUILD/boru-1.txt" \
  "カット1　0.0-3.6秒" \
  "オレンジのボールの横" \
  "黒猫が座って止まっている" \
  "まばたき1回。前足は床。ボールには触れていない"
write_card "$BUILD/boru-2.txt" \
  "カット2　3.6-7.0秒" \
  "同じ画角" \
  "視線だけがボールへ1回下りる" \
  "頭は下げない。口は閉じている"
write_card "$BUILD/boru-3.txt" \
  "カット3　7.0-10.2秒" \
  "同じ画角" \
  "しっぽの先が1回揺れて止まる" \
  "体は座ったまま。ボールは転がらない"
write_card "$BUILD/boru-4.txt" \
  "カット4　10.2-13.0秒" \
  "同じ画角" \
  "もう1回、ゆっくりまばたき" \
  "前足は床。ボールには触れない"
write_card "$BUILD/boru-5.txt" \
  "カット4のまま　13.0-15.0秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上のPRは残す。人は映っていない"
render "2026-11-09-ペット-kuroneko-boru" 15 360 336 13 \
  0 3.6 "$BUILD/boru-1.txt" \
  3.6 7.0 "$BUILD/boru-2.txt" \
  7.0 10.2 "$BUILD/boru-3.txt" \
  10.2 13 "$BUILD/boru-4.txt" \
  13 - "$BUILD/boru-5.txt"

# ペット 座布団（台本: 0.0-3.6 / 3.6-7.0 / 7.0-10.2 / 10.2-15.0。13.0-15.0は少し暗くする。尺15.0秒）
write_card "$BUILD/zabuton-1.txt" \
  "カット1　0.0-3.6秒" \
  "水色の四角い座布団の上" \
  "黒猫が体を起こして座っている" \
  "まばたき1回。前足2本は手前" \
  "丸まっていない。日光の四角は無い"
write_card "$BUILD/zabuton-2.txt" \
  "カット2　3.6-7.0秒" \
  "同じ画角" \
  "耳が1回動いて止まる" \
  "体は起きたまま。横にならない"
write_card "$BUILD/zabuton-3.txt" \
  "カット3　7.0-10.2秒" \
  "同じ画角" \
  "頭が少し横へ向いて止まる" \
  "体は起きている。丸まらない"
write_card "$BUILD/zabuton-4.txt" \
  "カット4　10.2-13.0秒" \
  "同じ画角" \
  "腹が息で1回ふくらんで戻る" \
  "座ったまま。前足は見えたまま"
write_card "$BUILD/zabuton-5.txt" \
  "カット4のまま　13.0-15.0秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上のPRは残す。前足は隠さない"
render "2026-11-10-ペット-kuroneko-zabuton" 15 360 336 13 \
  0 3.6 "$BUILD/zabuton-1.txt" \
  3.6 7.0 "$BUILD/zabuton-2.txt" \
  7.0 10.2 "$BUILD/zabuton-3.txt" \
  10.2 13 "$BUILD/zabuton-4.txt" \
  13 - "$BUILD/zabuton-5.txt"

# 金メモ 付加年金（台本: 0.0-3.0 / 3.0-9.0 / 9.0-15.0。PRなし。尺15.0秒）
# 右の金額は 0.0-3.0。40年の行は 3.0、5年の行は 6.2、943,300円の行は 9.2。
# 12,000円は 6.2 まで出さない。943,300円は 9.2 まで出さない。数字は台本の表のまま。
NAME="2026-11-06-金メモ-fuka-nenkin"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/fuka-right-big.txt" "40年 → 年96,000円"
write_card "$BUILD/fuka-right-small.txt" "20歳から60歳の例"
write_card "$BUILD/fuka-head.txt" "日本年金機構の例。200円×納付月数"
write_card "$BUILD/fuka-row-month.txt" "付加保険料 → 月400円"
write_card "$BUILD/fuka-row40.txt" \
  "20歳から60歳まで40年（480月）の例" \
  "年96,000円（200円×480月）"
write_card "$BUILD/fuka-row5.txt" \
  "60歳から65歳まで5年（60月）の例" \
  "年12,000円（60月×200円）"
write_card "$BUILD/fuka-row-sum.txt" \
  "40年の満額の老齢基礎に付加を足した例" \
  "年943,300円（847,300＋96,000）" \
  "昭和31年4月2日以後生まれ"
write_card "$BUILD/fuka-target.txt" "国民年金の第1号、または65歳未満の任意加入"
write_card "$BUILD/fuka-foot.txt" \
  "200円×納付した月数" \
  "物価スライドはない（定額）" \
  "国民年金基金の加入員は納付できない"
write_card "$BUILD/fuka-src.txt" "出典：日本年金機構"
write_card "$BUILD/fuka-credit.txt" "VOICEVOX:冥鳴ひまり"
add_text "$OV" "$BUILD/fuka-right-big.txt" 42 white "w-text_w-80" 860 'lt(t\,3)'
add_text "$OV" "$BUILD/fuka-right-small.txt" 28 white "w-text_w-80" 916 'lt(t\,3)'
add_text "$OV" "$BUILD/fuka-head.txt" 30 white 40 680 'gte(t\,3)'
add_text "$OV" "$BUILD/fuka-row-month.txt" 28 white 40 760 'gte(t\,3)*lt(t\,6.2)'
add_text "$OV" "$BUILD/fuka-row-month.txt" 28 0xBDBDBD 40 760 'gte(t\,6.2)'
add_text "$OV" "$BUILD/fuka-row40.txt" 28 white 40 830 'gte(t\,3)*lt(t\,6.2)'
add_text "$OV" "$BUILD/fuka-row40.txt" 28 0xBDBDBD 40 830 'gte(t\,6.2)'
add_text "$OV" "$BUILD/fuka-row5.txt" 28 white 40 960 'gte(t\,6.2)*lt(t\,9.2)'
add_text "$OV" "$BUILD/fuka-row5.txt" 28 0xBDBDBD 40 960 'gte(t\,9.2)'
add_text "$OV" "$BUILD/fuka-row-sum.txt" 28 white 40 1090 'gte(t\,9.2)*lt(t\,12.6)'
add_text "$OV" "$BUILD/fuka-row-sum.txt" 28 0xBDBDBD 40 1090 'gte(t\,12.6)'
add_text "$OV" "$BUILD/fuka-target.txt" 28 white 40 1280 'gte(t\,12.6)'
add_text "$OV" "$BUILD/fuka-foot.txt" 24 0xE6E6E6 40 1380 'gte(t\,3)'
add_text "$OV" "$BUILD/fuka-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/fuka-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,0)'
write_card "$BUILD/fuka-1.txt" \
  "カット1　0.0-3.0秒" \
  "文字の無い納付書を持つ成人" \
  "目を丸くして止まっている" \
  "右に年96,000円。人物は成人だけ"
write_card "$BUILD/fuka-2.txt" \
  "カット2　3.0-9.0秒" \
  "同じ成人が左下で納付書を机に置く" \
  "中央に早見表" \
  "人物は成人だけ"
write_card "$BUILD/fuka-3.txt" \
  "カット3　9.0-15.0秒" \
  "同じ成人が納付書を横に置く" \
  "うなずく。指はささない" \
  "表は上に残す。人物は成人だけ"
render "$NAME" 15 360 336 "" \
  0 3 "$BUILD/fuka-1.txt" \
  3 9 "$BUILD/fuka-2.txt" \
  9 - "$BUILD/fuka-3.txt"

# 金メモ 介護休業（台本: 0.0-3.0 / 3.0-9.0 / 9.0-15.0。PRなし。尺15.0秒）
# 行は 3.0、6.4、9.8、12.6。546,600円は 6.4 まで、93日は 9.8 まで出さない。円は台本の表のまま。
NAME="2026-11-07-金メモ-kaigo-kyugyo"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/kaigo-right-big.txt" "67% → 366,222円"
write_card "$BUILD/kaigo-right-small.txt" "1か月の上限"
write_card "$BUILD/kaigo-head.txt" "ハローワーク・令和9年7月31日までの上限"
write_card "$BUILD/kaigo-row67.txt" \
  "原則の支給率（支給日数30日・上限超過時）" \
  "1支給対象期間の上限 → 67%・366,222円"
write_card "$BUILD/kaigo-row-wage.txt" \
  "休業開始時の賃金月額の上限" \
  "超えるときはこの額で計算 → 546,600円"
write_card "$BUILD/kaigo-row-days.txt" "同じ家族 → 93日を限度に3回まで"
write_card "$BUILD/kaigo-row-80.txt" "賃金だけで80%以上は不支給"
write_card "$BUILD/kaigo-foot.txt" \
  "令和9年7月31日まで。毎年8月1日に変わる" \
  "賃金月額が96,090円を下回るときは96,090円で計算" \
  "就業している日が10日を超える支給単位期間は対象外"
write_card "$BUILD/kaigo-src.txt" "出典：ハローワーク"
write_card "$BUILD/kaigo-credit.txt" "VOICEVOX:冥鳴ひまり"
add_text "$OV" "$BUILD/kaigo-right-big.txt" 42 white "w-text_w-80" 860 'lt(t\,3)'
add_text "$OV" "$BUILD/kaigo-right-small.txt" 28 white "w-text_w-80" 916 'lt(t\,3)'
add_text "$OV" "$BUILD/kaigo-head.txt" 30 white 40 680 'gte(t\,3)'
add_text "$OV" "$BUILD/kaigo-row67.txt" 28 white 40 760 'gte(t\,3)*lt(t\,6.4)'
add_text "$OV" "$BUILD/kaigo-row67.txt" 28 0xBDBDBD 40 760 'gte(t\,6.4)'
add_text "$OV" "$BUILD/kaigo-row-wage.txt" 28 white 40 900 'gte(t\,6.4)*lt(t\,9.8)'
add_text "$OV" "$BUILD/kaigo-row-wage.txt" 28 0xBDBDBD 40 900 'gte(t\,9.8)'
add_text "$OV" "$BUILD/kaigo-row-days.txt" 28 white 40 1040 'gte(t\,9.8)*lt(t\,12.6)'
add_text "$OV" "$BUILD/kaigo-row-days.txt" 28 0xBDBDBD 40 1040 'gte(t\,12.6)'
add_text "$OV" "$BUILD/kaigo-row-80.txt" 30 white 40 1160 'gte(t\,12.6)'
add_text "$OV" "$BUILD/kaigo-foot.txt" 24 0xE6E6E6 40 1280 'gte(t\,3)'
add_text "$OV" "$BUILD/kaigo-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/kaigo-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,0)'
write_card "$BUILD/kaigo-1.txt" \
  "カット1　0.0-3.0秒" \
  "家の鍵と白紙のカレンダーの前の成人" \
  "目を丸くして止まっている" \
  "右に366,222円。人物は成人だけ"
write_card "$BUILD/kaigo-2.txt" \
  "カット2　3.0-9.0秒" \
  "同じ成人が左下で鍵を机に置く" \
  "中央に早見表" \
  "人物は成人だけ"
write_card "$BUILD/kaigo-3.txt" \
  "カット3　9.0-15.0秒" \
  "同じ成人がカレンダーを一度見る" \
  "指はささない。表は上に残す" \
  "人物は成人だけ。子どもの絵は無い"
render "$NAME" 15 360 336 "" \
  0 3 "$BUILD/kaigo-1.txt" \
  3 9 "$BUILD/kaigo-2.txt" \
  9 - "$BUILD/kaigo-3.txt"

# 金メモ 高年齢雇用継続（台本: 0.0-3.0 / 3.0-9.0 / 9.0-15.0。PRなし。尺15.0秒）
# 行は 3.0、6.4、9.4、12.0。15%は 9.4 まで、397,369円は 12.0 まで出さない。円は台本の表のまま。
NAME="2026-11-08-金メモ-kounenrei-keizoku"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/kou-right-big.txt" "30万→18万で 18,000円"
write_card "$BUILD/kou-right-small.txt" "公式の例"
write_card "$BUILD/kou-head.txt" "高年齢雇用継続基本給付金・5年以上・60歳以上65歳未満"
write_card "$BUILD/kou-row-ex.txt" \
  "賃金月額30万円、その月18万円" \
  "低下率60%（64%以下）の例" \
  "18万円×10%＝18,000円"
write_card "$BUILD/kou-row-10.txt" \
  "60歳に達した日、または5年を満たした日" \
  "令和7年4月1日以降 → 最大10%" \
  "64%以下ならその月の賃金の10%"
write_card "$BUILD/kou-row-15.txt" \
  "その日が令和7年3月31日以前" \
  "最大15%（61%以下のとき）" \
  "61%を超えて75%未満は、15%より少ない"
write_card "$BUILD/kou-row-cap.txt" \
  "その月の賃金が397,369円以上" \
  "支給されない（令和9年7月31日までの限度額）"
write_card "$BUILD/kou-foot.txt" \
  "75%未満に下がった月が対象" \
  "算定した支給額が2,562円以下のときも支給されない" \
  "60歳到達時の賃金月額は522,000円を超えると522,000円" \
  "96,090円を下回ると96,090円" \
  "この3つの円は令和9年7月31日まで"
write_card "$BUILD/kou-src.txt" "出典：厚生労働省"
write_card "$BUILD/kou-credit.txt" "VOICEVOX:冥鳴ひまり"
add_text "$OV" "$BUILD/kou-right-big.txt" 40 white "w-text_w-80" 860 'lt(t\,3)'
add_text "$OV" "$BUILD/kou-right-small.txt" 28 white "w-text_w-80" 916 'lt(t\,3)'
add_text "$OV" "$BUILD/kou-head.txt" 28 white 40 660 'gte(t\,3)'
add_text "$OV" "$BUILD/kou-row-ex.txt" 28 white 40 740 'gte(t\,3)*lt(t\,6.4)'
add_text "$OV" "$BUILD/kou-row-ex.txt" 28 0xBDBDBD 40 740 'gte(t\,6.4)'
add_text "$OV" "$BUILD/kou-row-10.txt" 28 white 40 900 'gte(t\,6.4)*lt(t\,9.4)'
add_text "$OV" "$BUILD/kou-row-10.txt" 28 0xBDBDBD 40 900 'gte(t\,9.4)'
add_text "$OV" "$BUILD/kou-row-15.txt" 28 white 40 1060 'gte(t\,9.4)*lt(t\,12)'
add_text "$OV" "$BUILD/kou-row-15.txt" 28 0xBDBDBD 40 1060 'gte(t\,12)'
add_text "$OV" "$BUILD/kou-row-cap.txt" 28 white 40 1220 'gte(t\,12)'
add_text "$OV" "$BUILD/kou-foot.txt" 22 0xE6E6E6 40 1340 'gte(t\,3)'
add_text "$OV" "$BUILD/kou-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/kou-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,0)'
write_card "$BUILD/kou-1.txt" \
  "カット1　0.0-3.0秒" \
  "大きい封筒と小さい封筒を持つ成人" \
  "目を丸くして止まっている" \
  "右に18,000円。人物は成人だけ"
write_card "$BUILD/kou-2.txt" \
  "カット2　3.0-9.0秒" \
  "同じ成人が左下で封筒2つを机に置く" \
  "中央に早見表" \
  "人物は成人だけ"
write_card "$BUILD/kou-3.txt" \
  "カット3　9.0-15.0秒" \
  "同じ成人が封筒を横にそろえてうなずく" \
  "指はささない。表は上に残す" \
  "人物は成人だけ"
render "$NAME" 15 360 336 "" \
  0 3 "$BUILD/kou-1.txt" \
  3 9 "$BUILD/kou-2.txt" \
  9 - "$BUILD/kou-3.txt"

echo "完了"
