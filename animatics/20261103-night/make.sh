#!/usr/bin/env bash
# 下書き動画（灰色の静止カード＋SRT焼き込み）。音は入れない。絵は描かない。生成AIは使わない。
# 字幕は同じフォルダの subs/（入力のSRTをそのまま）。台本ファイルはコミットしない。
# 使い方: bash animatics/20261103-night/make.sh
# 1本だけ: ONLY=<名前> bash animatics/20261103-night/make.sh
#
# カードの秒は台本のカットどおり。字幕の文言と時刻は変えない。
# ffmpeg が SRT を ASS にすると PlayRes が 384x288 になり、9:16 では字が縦に伸びる。
# 直すのは PlayRes と字体だけ（1080x1920、文泉驛微米黑、画面上で約40px）。
# 金メモの台詞行には位置タグが無い。焼き込み時だけ下（{\an2}）にする。文言と時刻はそのまま。
# 早見表・右の金額・出典・クレジットは、台本の画面文字を編集の文字として載せる。SRTには入れない。
# いらすとやの画像は使っていないので、「イラスト：いらすとや」は載せない。
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
BUILD=${BUILD:-/tmp/animatic-build-20261103-night}
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

# 金メモ 在職老齢年金（台本: 0.0-3.0 / 3.0-9.0 / 9.0-15.0。PRなし。尺15.0秒）
# 右の金額は 0.0-3.0。基準の行は 3.0、例の行は 6.0、60万円のマスは 9.2、注記は 12.4。
# 2万5千円は 9.2 まで出さない。円は台本の表のまま。式から作った円は出さない。
NAME="2026-11-12-金メモ-zaishoku-rourei"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/zai-right-big.txt" "65万円"
write_card "$BUILD/zai-right-small.txt" "令和8年度の基準"
write_card "$BUILD/zai-head.txt" "令和8年4月以降・日本年金機構"
write_card "$BUILD/zai-row65.txt" \
  "65万円以下は全額支給" \
  "引き上げ前は51万円"
write_card "$BUILD/zai-row46.txt" \
  "賃金46万円・老齢厚生年金10万円" \
  "2026年4月から停止なし"
write_card "$BUILD/zai-row25.txt" \
  "基本月額10万円・総報酬月額相当額60万円" \
  "停止2万5千円"
write_card "$BUILD/zai-note.txt" "老齢基礎年金は減額されない"
write_card "$BUILD/zai-foot.txt" \
  "基本月額は、加給年金額を除いた" \
  "老齢厚生年金（報酬比例部分）の月額" \
  "総報酬月額相当額は、その月の標準報酬月額" \
  "＋その月以前1年の標準賞与額の合計÷12" \
  "65万円は令和8年度の額。毎年度改定"
write_card "$BUILD/zai-foot25.txt" "2万5千円はPDFの2.5（単位：万円）"
write_card "$BUILD/zai-src.txt" "出典：日本年金機構"
write_card "$BUILD/zai-credit.txt" "VOICEVOX:冥鳴ひまり"
add_text "$OV" "$BUILD/zai-right-big.txt" 40 white "w-text_w-80" 860 'lt(t\,3)'
add_text "$OV" "$BUILD/zai-right-small.txt" 26 white "w-text_w-80" 916 'lt(t\,3)'
add_text "$OV" "$BUILD/zai-head.txt" 28 white 40 660 'gte(t\,3)'
add_text "$OV" "$BUILD/zai-row65.txt" 26 white 40 740 'gte(t\,3)*lt(t\,6)'
add_text "$OV" "$BUILD/zai-row65.txt" 26 0xBDBDBD 40 740 'gte(t\,6)'
add_text "$OV" "$BUILD/zai-row46.txt" 26 white 40 840 'gte(t\,6)*lt(t\,9.2)'
add_text "$OV" "$BUILD/zai-row46.txt" 26 0xBDBDBD 40 840 'gte(t\,9.2)'
add_text "$OV" "$BUILD/zai-row25.txt" 26 white 40 960 'gte(t\,9.2)*lt(t\,12.4)'
add_text "$OV" "$BUILD/zai-row25.txt" 26 0xBDBDBD 40 960 'gte(t\,12.4)'
add_text "$OV" "$BUILD/zai-note.txt" 26 white 40 1080 'gte(t\,12.4)'
add_text "$OV" "$BUILD/zai-foot.txt" 22 0xE6E6E6 40 1180 'gte(t\,3)'
add_text "$OV" "$BUILD/zai-foot25.txt" 22 0xE6E6E6 40 1360 'gte(t\,9.2)'
add_text "$OV" "$BUILD/zai-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/zai-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,0)'
write_card "$BUILD/zai-1.txt" \
  "カット1　0.0-3.0秒" \
  "無地の白いタイムカードを持つ成人" \
  "目を丸くして止まっている" \
  "右に65万円。人物は成人だけ"
write_card "$BUILD/zai-2.txt" \
  "カット2　3.0-9.0秒" \
  "同じ成人が左下でタイムカードを机に置く" \
  "中央に早見表" \
  "人物は成人だけ"
write_card "$BUILD/zai-3.txt" \
  "カット3　9.0-15.0秒" \
  "同じ成人がタイムカードを横に置く" \
  "うなずく。指はささない" \
  "表は上に残す。人物は成人だけ"
render "$NAME" 15 360 336 "" \
  0 3 "$BUILD/zai-1.txt" \
  3 9 "$BUILD/zai-2.txt" \
  9 - "$BUILD/zai-3.txt"

# 金メモ 埋葬料（台本: 0.0-3.0 / 3.0-9.0 / 9.0-15.0。PRなし。尺15.0秒）
# 行は 3.0、6.2、9.2。注記は 12.4。円は台本の表の50,000円だけ。
# 埋葬費の行は「50,000円の範囲内」。費目ごとの円は出さない。
NAME="2026-11-13-金メモ-maisou-ryo"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/mai-right-big.txt" "50,000円"
write_card "$BUILD/mai-right-small.txt" "埋葬料"
write_card "$BUILD/mai-head.txt" "協会けんぽ・業務外"
write_card "$BUILD/mai-row1.txt" \
  "埋葬料。被保険者により生計を維持されていた人が申請" \
  "50,000円"
write_card "$BUILD/mai-row2.txt" \
  "埋葬費。その人がいないときだけ" \
  "埋葬を行った人が申請" \
  "50,000円の範囲内"
write_card "$BUILD/mai-row3.txt" \
  "家族埋葬費。被扶養者が亡くなり、被保険者が申請" \
  "50,000円"
write_card "$BUILD/mai-note.txt" "業務外。申請書を協会けんぽ支部へ"
write_card "$BUILD/mai-foot.txt" \
  "業務外" \
  "5万円は50,000円" \
  "埋葬料と埋葬費は、どちらか" \
  "給付ページの表は「家族埋葬費」" \
  "同じページの導入は「家族埋葬料」とも書いている"
write_card "$BUILD/mai-src.txt" "出典：協会けんぽ"
write_card "$BUILD/mai-credit.txt" "VOICEVOX:冥鳴ひまり"
add_text "$OV" "$BUILD/mai-right-big.txt" 40 white "w-text_w-80" 860 'lt(t\,3)'
add_text "$OV" "$BUILD/mai-right-small.txt" 26 white "w-text_w-80" 916 'lt(t\,3)'
add_text "$OV" "$BUILD/mai-head.txt" 28 white 40 660 'gte(t\,3)'
add_text "$OV" "$BUILD/mai-row1.txt" 26 white 40 740 'gte(t\,3)*lt(t\,6.2)'
add_text "$OV" "$BUILD/mai-row1.txt" 26 0xBDBDBD 40 740 'gte(t\,6.2)'
add_text "$OV" "$BUILD/mai-row2.txt" 26 white 40 860 'gte(t\,6.2)*lt(t\,9.2)'
add_text "$OV" "$BUILD/mai-row2.txt" 26 0xBDBDBD 40 860 'gte(t\,9.2)'
add_text "$OV" "$BUILD/mai-row3.txt" 26 white 40 1020 'gte(t\,9.2)*lt(t\,12.4)'
add_text "$OV" "$BUILD/mai-row3.txt" 26 0xBDBDBD 40 1020 'gte(t\,12.4)'
add_text "$OV" "$BUILD/mai-note.txt" 26 white 40 1160 'gte(t\,12.4)'
add_text "$OV" "$BUILD/mai-foot.txt" 22 0xE6E6E6 40 1260 'gte(t\,3)'
add_text "$OV" "$BUILD/mai-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/mai-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,0)'
write_card "$BUILD/mai-1.txt" \
  "カット1　0.0-3.0秒" \
  "無地の白い花を1輪持つ成人" \
  "目を丸くして止まっている" \
  "右に50,000円。人物は成人だけ。子どもの絵は無い"
write_card "$BUILD/mai-2.txt" \
  "カット2　3.0-9.0秒" \
  "同じ成人が左下で花を机に置く" \
  "中央に早見表" \
  "人物は成人だけ"
write_card "$BUILD/mai-3.txt" \
  "カット3　9.0-15.0秒" \
  "同じ成人が花を横に置く" \
  "うなずく。指はささない" \
  "表は上に残す。人物は成人だけ"
render "$NAME" 15 360 336 "" \
  0 3 "$BUILD/mai-1.txt" \
  3 9 "$BUILD/mai-2.txt" \
  9 - "$BUILD/mai-3.txt"

# 金メモ 育児時短就業給付（台本: 0.0-3.0 / 3.0-9.0 / 9.0-15.0。PRなし。尺15.0秒）
# 20,000円の行は 3.0。開始時300,000円とその月200,000円は 5.8 で明るい。
# 270,000円は 9.2 まで出さない。注記は 12.4。Q74の例（2）の円は出さない。子どもの絵は出さない。
NAME="2026-11-14-金メモ-ikuji-jitan"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/iku-right-big.txt" "20,000円"
write_card "$BUILD/iku-right-small.txt" "この例・月20万円のとき"
write_card "$BUILD/iku-head.txt" "厚生労働省の例・90%以下は10%"
write_card "$BUILD/iku-row20.txt" \
  "その月の賃金が200,000円（開始時の90%以下）" \
  "20,000円（10%）"
write_card "$BUILD/iku-row30.txt" \
  "育児時短就業開始時賃金月額" \
  "300,000円"
write_card "$BUILD/iku-row27.txt" \
  "90%のライン" \
  "270,000円"
write_card "$BUILD/iku-note.txt" "2歳の誕生日の前々日が属する月まで。要件あり"
write_card "$BUILD/iku-foot.txt" \
  "90%以下の月は、その月の賃金×10%" \
  "90%を超えて100%未満の月は、支給率が下がる" \
  "100%以上の月、支給限度額以上の月、" \
  "最低限度額以下の月は、その月は不支給" \
  "限度額の円は、開いた本文と支給率の画像に無かった"
write_card "$BUILD/iku-src.txt" "出典：厚生労働省"
write_card "$BUILD/iku-credit.txt" "VOICEVOX:冥鳴ひまり"
add_text "$OV" "$BUILD/iku-right-big.txt" 40 white "w-text_w-80" 860 'lt(t\,3)'
add_text "$OV" "$BUILD/iku-right-small.txt" 26 white "w-text_w-80" 916 'lt(t\,3)'
add_text "$OV" "$BUILD/iku-head.txt" 28 white 40 660 'gte(t\,3)'
add_text "$OV" "$BUILD/iku-row20.txt" 26 white 40 740 'gte(t\,3)*lt(t\,9.2)'
add_text "$OV" "$BUILD/iku-row20.txt" 26 0xBDBDBD 40 740 'gte(t\,9.2)'
add_text "$OV" "$BUILD/iku-row30.txt" 26 white 40 860 'gte(t\,5.8)*lt(t\,9.2)'
add_text "$OV" "$BUILD/iku-row30.txt" 26 0xBDBDBD 40 860 'gte(t\,9.2)'
add_text "$OV" "$BUILD/iku-row27.txt" 26 white 40 980 'gte(t\,9.2)*lt(t\,12.4)'
add_text "$OV" "$BUILD/iku-row27.txt" 26 0xBDBDBD 40 980 'gte(t\,12.4)'
add_text "$OV" "$BUILD/iku-note.txt" 26 white 40 1100 'gte(t\,12.4)'
add_text "$OV" "$BUILD/iku-foot.txt" 22 0xE6E6E6 40 1200 'gte(t\,3)'
add_text "$OV" "$BUILD/iku-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/iku-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,0)'
write_card "$BUILD/iku-1.txt" \
  "カット1　0.0-3.0秒" \
  "針も数字も無い丸い時計を持つ成人" \
  "目を丸くして止まっている" \
  "右に20,000円。人物は成人だけ。子どもの絵は無い"
write_card "$BUILD/iku-2.txt" \
  "カット2　3.0-9.0秒" \
  "同じ成人が左下で時計を机に置く" \
  "中央に早見表" \
  "人物は成人だけ"
write_card "$BUILD/iku-3.txt" \
  "カット3　9.0-15.0秒" \
  "同じ成人が時計を横に置く" \
  "うなずく。指はささない" \
  "表は上に残す。人物は成人だけ。子どもの絵は無い"
render "$NAME" 15 360 336 "" \
  0 3 "$BUILD/iku-1.txt" \
  3 9 "$BUILD/iku-2.txt" \
  9 - "$BUILD/iku-3.txt"

echo "完了"
