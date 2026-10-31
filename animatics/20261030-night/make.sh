#!/usr/bin/env bash
# 下書き動画（灰色の静止カード＋SRT焼き込み）。音は入れない。絵は描かない。生成AIは使わない。
# 字幕は同じフォルダの subs/（入力のSRTをそのまま）。台本ファイルはコミットしない。
# 使い方: bash animatics/20261030-night/make.sh
# 1本だけ: ONLY=<名前> bash animatics/20261030-night/make.sh
#
# カードの秒は台本のカットどおり。字幕の文言と時刻は変えない。
# ffmpeg が SRT を ASS にすると PlayRes が 384x288 になり、9:16 では字が縦に伸びる。
# 直すのは PlayRes と字体だけ（1080x1920、文泉驛微米黑、画面上で約40px）。
# 金メモの台詞行には位置タグが無い。焼き込み時だけ下（{\an2}）にする。文言と時刻はそのまま。
# 早見表・右の金額・出典・クレジットは、台本の画面文字を編集の文字として載せる。SRTには入れない。
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
BUILD=${BUILD:-/tmp/animatic-build-20261030-night}
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

# ペット 爪とぎ（台本: 0.0-3.6 / 3.6-7.0 / 7.0-10.2 / 10.2-15.0。13.0-15.0は少し暗くする。尺15.0秒）
write_card "$BUILD/tsumetogi-1.txt" \
  "カット1　0.0-3.6秒" \
  "縦型の爪とぎの横" \
  "黒猫が座って止まっている" \
  "まばたき1回。前足は床。人は映っていない"
write_card "$BUILD/tsumetogi-2.txt" \
  "カット2　3.6-7.0秒" \
  "同じ画角" \
  "耳が1回、爪とぎの方へ向く" \
  "体と前足は動かない"
write_card "$BUILD/tsumetogi-3.txt" \
  "カット3　7.0-10.2秒" \
  "同じ画角。前足は床のまま" \
  "目を少し細める" \
  "爪とぎには触れていない"
write_card "$BUILD/tsumetogi-4.txt" \
  "カット4　10.2-13.0秒" \
  "同じ画角" \
  "座ったまま、とがない" \
  "人は映っていない"
write_card "$BUILD/tsumetogi-5.txt" \
  "カット4のまま　13.0-15.0秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上のPRは残す"
render "2026-11-05-ペット-kuroneko-tsumetogi" 15 360 336 13 \
  0 3.6 "$BUILD/tsumetogi-1.txt" \
  3.6 7.0 "$BUILD/tsumetogi-2.txt" \
  7.0 10.2 "$BUILD/tsumetogi-3.txt" \
  10.2 13 "$BUILD/tsumetogi-4.txt" \
  13 - "$BUILD/tsumetogi-5.txt"

# ペット 丸まり（台本: 0.0-3.6 / 3.6-7.0 / 7.0-10.2 / 10.2-15.0。13.0-15.0は少し暗くする。尺15.0秒）
write_card "$BUILD/marumaku-1.txt" \
  "カット1　0.0-3.6秒" \
  "黄色のドーナツ型ベッド" \
  "黒猫が輪の中で丸まっている" \
  "目は開いている。前足2本は輪の手前" \
  "人は映っていない。日光の四角は無い"
write_card "$BUILD/marumaku-2.txt" \
  "カット2　3.6-7.0秒" \
  "同じ画角" \
  "しっぽの先が1回揺れて止まる" \
  "体は丸まったまま。前足は動かない"
write_card "$BUILD/marumaku-3.txt" \
  "カット3　7.0-10.2秒" \
  "同じ画角" \
  "頭が少し横へ向いて止まる" \
  "体は伸びない。前足は動かない"
write_card "$BUILD/marumaku-4.txt" \
  "カット4　10.2-13.0秒" \
  "同じ画角" \
  "腹が息で1回ふくらんで戻る" \
  "ベッドから出ない。前足は見えたまま"
write_card "$BUILD/marumaku-5.txt" \
  "カット4のまま　13.0-15.0秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上のPRは残す"
render "2026-11-06-ペット-kuroneko-marumaku" 15 360 336 13 \
  0 3.6 "$BUILD/marumaku-1.txt" \
  3.6 7.0 "$BUILD/marumaku-2.txt" \
  7.0 10.2 "$BUILD/marumaku-3.txt" \
  10.2 13 "$BUILD/marumaku-4.txt" \
  13 - "$BUILD/marumaku-5.txt"

# ペット 空の器（台本: 0.0-3.0 / 3.0-5.0 / 5.0-15.0。13.0-15.0は少し暗くする。尺15.0秒）
write_card "$BUILD/utsawa-1.txt" \
  "カット1　0.0-3.0秒" \
  "空のクリーム色の浅い器" \
  "黒猫が横に座って止まっている" \
  "まばたき1回。顔は器の外。人は映っていない"
write_card "$BUILD/utsawa-2.txt" \
  "カット2　3.0-5.0秒" \
  "同じ画角" \
  "視線だけが器の内側へ1回下りる" \
  "頭は下げない。口は閉じている"
write_card "$BUILD/utsawa-3.txt" \
  "カット3　5.0-13.0秒" \
  "同じ画角。顔は器の外" \
  "口は閉じたまま。器に触れていない" \
  "新しい動きは無い。獣医は映さない"
write_card "$BUILD/utsawa-4.txt" \
  "カット3のまま　13.0-15.0秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上のPRは残す。獣医は映さない"
render "2026-11-07-ペット-kuroneko-utsawa" 15 360 336 13 \
  0 3 "$BUILD/utsawa-1.txt" \
  3 5 "$BUILD/utsawa-2.txt" \
  5 13 "$BUILD/utsawa-3.txt" \
  13 - "$BUILD/utsawa-4.txt"

# 金メモ 医療費控除（台本: 0.0-3.0 / 3.0-9.0 / 9.0-15.0。PRなし。尺15.0秒）
# 右の金額は 0.0-3.0。表の行は 6.2、9.2、12.2 に1行ずつ。数字は台本の表のまま。
NAME="2026-11-03-金メモ-iryohi-kojo"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/iryohi-right-big.txt" "10万円を引く"
write_card "$BUILD/iryohi-right-small.txt" "総所得金額等200万円以上"
write_card "$BUILD/iryohi-head.txt" "国税庁 No.1120・支払った医療費から"
write_card "$BUILD/iryohi-note.txt" "保険金などで補てんされる金額を先に引く"
write_card "$BUILD/iryohi-row1.txt" "総所得金額等が200万円以上 → 10万円を引く"
write_card "$BUILD/iryohi-row2.txt" "控除額の上限 → 最高200万円"
write_card "$BUILD/iryohi-row3.txt" "総所得金額等が200万円未満 → 総所得金額等の5パーセントを引く"
write_card "$BUILD/iryohi-foot.txt" \
  "先に、保険金などで補てんされる金額を引く" \
  "控除額であり、還付額そのものではない" \
  "令和8年4月1日現在法令等"
write_card "$BUILD/iryohi-src.txt" "出典：国税庁 No.1120"
write_card "$BUILD/iryohi-credit.txt" "VOICEVOX:冥鳴ひまり"
add_text "$OV" "$BUILD/iryohi-right-big.txt" 42 white "w-text_w-80" 980 'lt(t\,3)'
add_text "$OV" "$BUILD/iryohi-right-small.txt" 28 white "w-text_w-80" 1036 'lt(t\,3)'
add_text "$OV" "$BUILD/iryohi-head.txt" 32 white 60 700 'gte(t\,3)'
add_text "$OV" "$BUILD/iryohi-note.txt" 30 white 60 780 'gte(t\,3)'
add_text "$OV" "$BUILD/iryohi-row1.txt" 30 white 60 880 'gte(t\,6.2)*lt(t\,9.2)'
add_text "$OV" "$BUILD/iryohi-row1.txt" 30 0xBDBDBD 60 880 'gte(t\,9.2)'
add_text "$OV" "$BUILD/iryohi-row2.txt" 30 white 60 960 'gte(t\,9.2)*lt(t\,12.2)'
add_text "$OV" "$BUILD/iryohi-row2.txt" 30 0xBDBDBD 60 960 'gte(t\,12.2)'
add_text "$OV" "$BUILD/iryohi-row3.txt" 30 white 60 1040 'gte(t\,12.2)'
add_text "$OV" "$BUILD/iryohi-foot.txt" 24 0xE6E6E6 60 1160 'gte(t\,3)'
add_text "$OV" "$BUILD/iryohi-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/iryohi-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,0)'
write_card "$BUILD/iryohi-1.txt" \
  "カット1　0.0-3.0秒" \
  "領収書の束を持つ成人" \
  "目を丸くして止まっている" \
  "右に「10万円を引く」。人物は成人だけ"
write_card "$BUILD/iryohi-2.txt" \
  "カット2　3.0-9.0秒" \
  "同じ成人が左下で領収書を机に置く" \
  "中央に早見表" \
  "人物は成人だけ"
write_card "$BUILD/iryohi-3.txt" \
  "カット3　9.0-15.0秒" \
  "同じ成人が領収書を横に置く" \
  "うなずく。指はささない" \
  "表は上に残す。人物は成人だけ"
render "$NAME" 15 360 336 "" \
  0 3 "$BUILD/iryohi-1.txt" \
  3 9 "$BUILD/iryohi-2.txt" \
  9 - "$BUILD/iryohi-3.txt"

# 金メモ 基本手当（台本: 0.0-3.0 / 3.0-9.0 / 9.0-15.0。PRなし。尺15.0秒）
# 行は 3.0、6.2、9.0、11.2。330日は 11.2 まで出さない。日数は台本の表のまま。
NAME="2026-11-04-金メモ-kihon-teate"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/kihon-right-big.txt" "20年以上 → 150日"
write_card "$BUILD/kihon-right-small.txt" "1及び3以外・全年齢"
write_card "$BUILD/kihon-head.txt" "ハローワーク・所定給付日数・1及び3以外（全年齢）"
write_card "$BUILD/kihon-row1.txt" "1及び3以外・1年以上10年未満（全年齢） → 90日"
write_card "$BUILD/kihon-row2.txt" "1及び3以外・10年以上20年未満（全年齢） → 120日"
write_card "$BUILD/kihon-row3.txt" "1及び3以外・20年以上（全年齢） → 150日"
write_card "$BUILD/kihon-row4-head.txt" "特定受給資格者・45歳以上60歳未満・20年以上"
write_card "$BUILD/kihon-row4.txt" "所定給付日数 → 330日"
write_card "$BUILD/kihon-foot.txt" \
  "1年以上10年未満は、1年以上5年未満と" \
  "5年以上10年未満がどちらも90日" \
  "日額はこの表に無い"
write_card "$BUILD/kihon-foot330.txt" \
  "330日は表1のその年齢・その年数の欄"
write_card "$BUILD/kihon-src.txt" "出典：ハローワーク"
write_card "$BUILD/kihon-credit.txt" "VOICEVOX:冥鳴ひまり"
add_text "$OV" "$BUILD/kihon-right-big.txt" 42 white "w-text_w-80" 980 'lt(t\,3)'
add_text "$OV" "$BUILD/kihon-right-small.txt" 28 white "w-text_w-80" 1036 'lt(t\,3)'
add_text "$OV" "$BUILD/kihon-head.txt" 30 white 40 700 'gte(t\,3)'
add_text "$OV" "$BUILD/kihon-row1.txt" 28 white 40 800 'gte(t\,3)*lt(t\,6.2)'
add_text "$OV" "$BUILD/kihon-row1.txt" 28 0xBDBDBD 40 800 'gte(t\,6.2)'
add_text "$OV" "$BUILD/kihon-row2.txt" 28 white 40 880 'gte(t\,6.2)*lt(t\,9)'
add_text "$OV" "$BUILD/kihon-row2.txt" 28 0xBDBDBD 40 880 'gte(t\,9)'
add_text "$OV" "$BUILD/kihon-row3.txt" 28 white 40 960 'gte(t\,9)*lt(t\,11.2)'
add_text "$OV" "$BUILD/kihon-row3.txt" 28 0xBDBDBD 40 960 'gte(t\,11.2)'
add_text "$OV" "$BUILD/kihon-row4-head.txt" 28 white 40 1060 'gte(t\,11.2)'
add_text "$OV" "$BUILD/kihon-row4.txt" 32 white 40 1120 'gte(t\,11.2)'
add_text "$OV" "$BUILD/kihon-foot.txt" 24 0xE6E6E6 40 1240 'gte(t\,3)'
add_text "$OV" "$BUILD/kihon-foot330.txt" 24 0xE6E6E6 40 1360 'gte(t\,11.2)'
add_text "$OV" "$BUILD/kihon-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/kihon-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,0)'
write_card "$BUILD/kihon-1.txt" \
  "カット1　0.0-3.0秒" \
  "文字の無い紙を持つ成人" \
  "目を丸くして止まっている" \
  "右に150日。人物は成人だけ"
write_card "$BUILD/kihon-2.txt" \
  "カット2　3.0-9.0秒" \
  "同じ成人が左下で紙を机に置く" \
  "中央に早見表" \
  "人物は成人だけ"
write_card "$BUILD/kihon-3.txt" \
  "カット3　9.0-15.0秒" \
  "同じ成人が紙を閉じてうなずく" \
  "指はささない。表は上に残す" \
  "人物は成人だけ"
render "$NAME" 15 360 336 "" \
  0 3 "$BUILD/kihon-1.txt" \
  3 9 "$BUILD/kihon-2.txt" \
  9 - "$BUILD/kihon-3.txt"

# 金メモ 育児休業給付（台本: 0.0-3.0 / 3.0-9.0 / 9.0-15.0。PRなし。尺15.0秒）
# 行は 3.0、6.2、9.4、12.2。円は台本の表のまま。子どもは描かない。
NAME="2026-11-05-金メモ-ikuji-kyufu"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/ikuji-right-big.txt" "67% → 332,454円"
write_card "$BUILD/ikuji-right-small.txt" "30日の上限"
write_card "$BUILD/ikuji-head.txt" "厚生労働省・令和9年7月31日までの支給上限額"
write_card "$BUILD/ikuji-row1.txt" \
  "育児休業給付金・通算180日まで・67%" \
  "支給日数30日の支給上限額 → 332,454円"
write_card "$BUILD/ikuji-row2.txt" \
  "育児休業給付金・181日目以降・50%" \
  "支給日数30日の支給上限額 → 248,100円"
write_card "$BUILD/ikuji-row3.txt" \
  "出生後休業支援給付金・13%（要件あり）" \
  "支給日数28日の支給上限額 → 60,205円"
write_card "$BUILD/ikuji-row4.txt" "休業開始時賃金日額の上限額 → 16,540円"
write_card "$BUILD/ikuji-foot-wage.txt" \
  "事業主から賃金が出ると、額は変わる"
write_card "$BUILD/ikuji-foot-13.txt" \
  "13%は、PDFの要件を満たす場合の上乗せ"
write_card "$BUILD/ikuji-foot-16540.txt" \
  "上限額。賃金日額が16,540円未満なら、" \
  "30日の支給上限額までは届かない"
write_card "$BUILD/ikuji-src.txt" "出典：厚生労働省"
write_card "$BUILD/ikuji-credit.txt" "VOICEVOX:冥鳴ひまり"
add_text "$OV" "$BUILD/ikuji-right-big.txt" 42 white "w-text_w-80" 980 'lt(t\,3)'
add_text "$OV" "$BUILD/ikuji-right-small.txt" 28 white "w-text_w-80" 1036 'lt(t\,3)'
add_text "$OV" "$BUILD/ikuji-head.txt" 30 white 40 680 'gte(t\,3)'
add_text "$OV" "$BUILD/ikuji-row1.txt" 30 white 40 760 'gte(t\,3)*lt(t\,6.2)'
add_text "$OV" "$BUILD/ikuji-row1.txt" 30 0xBDBDBD 40 760 'gte(t\,6.2)'
add_text "$OV" "$BUILD/ikuji-row2.txt" 30 white 40 880 'gte(t\,6.2)*lt(t\,9.4)'
add_text "$OV" "$BUILD/ikuji-row2.txt" 30 0xBDBDBD 40 880 'gte(t\,9.4)'
add_text "$OV" "$BUILD/ikuji-row3.txt" 30 white 40 1000 'gte(t\,9.4)*lt(t\,12.2)'
add_text "$OV" "$BUILD/ikuji-row3.txt" 30 0xBDBDBD 40 1000 'gte(t\,12.2)'
add_text "$OV" "$BUILD/ikuji-row4.txt" 30 white 40 1140 'gte(t\,12.2)'
add_text "$OV" "$BUILD/ikuji-foot-wage.txt" 24 0xE6E6E6 40 1280 'gte(t\,3)'
add_text "$OV" "$BUILD/ikuji-foot-13.txt" 24 0xE6E6E6 40 1340 'gte(t\,9.4)'
add_text "$OV" "$BUILD/ikuji-foot-16540.txt" 24 0xE6E6E6 40 1400 'gte(t\,12.2)'
add_text "$OV" "$BUILD/ikuji-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/ikuji-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,0)'
write_card "$BUILD/ikuji-1.txt" \
  "カット1　0.0-3.0秒" \
  "文字の無い申請用紙を持つ成人" \
  "目を丸くして止まっている" \
  "右に332,454円。人物は成人だけ"
write_card "$BUILD/ikuji-2.txt" \
  "カット2　3.0-9.0秒" \
  "同じ成人が左下で用紙を机に置く" \
  "中央に早見表" \
  "人物は成人だけ"
write_card "$BUILD/ikuji-3.txt" \
  "カット3　9.0-15.0秒" \
  "同じ成人が用紙を横に置いてうなずく" \
  "指はささない。表は上に残す" \
  "人物は成人だけ"
render "$NAME" 15 360 336 "" \
  0 3 "$BUILD/ikuji-1.txt" \
  3 9 "$BUILD/ikuji-2.txt" \
  9 - "$BUILD/ikuji-3.txt"

echo "完了"
