#!/usr/bin/env bash
# 下書き動画（灰色の静止カード＋SRT焼き込み）。音は入れない。絵は描かない。生成AIは使わない。
# 字幕は同じフォルダの subs/（入力のSRTをそのまま）。台本ファイルはコミットしない。
# 使い方: bash animatics/20261104-night/make.sh
# 1本だけ: ONLY=<名前> bash animatics/20261104-night/make.sh
#
# カードの秒は台本のカットどおり。字幕の文言と時刻は変えない。
# ffmpeg が SRT を ASS にすると PlayRes が 384x288 になり、9:16 では字が縦に伸びる。
# 直すのは PlayRes と字体だけ（1080x1920、文泉驛微米黑、画面上で約40px）。
# 金メモの台詞行には位置タグが無い。焼き込み時だけ下（{\an2}）にする。文言と時刻はそのまま。
# 早見表・右の金額・出典・クレジットは、台本の画面文字を編集の文字として載せる。SRTには入れない。
# いらすとやの画像は使っていないので、「イラスト：いらすとや」は載せない。
# ペットの右上PRは、台本が削除しSRTにも無いので足さない。最後の「広告 #PR」はSRTの {\an5}。
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
BUILD=${BUILD:-/tmp/animatic-build-20261104-night}
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
    -an \
    -c:v libx264 -pix_fmt yuv420p -r 24 -fps_mode cfr \
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

# ペット ばね（台本: 0.0-3.0 / 3.0-6.0 / 6.0-8.5 / 8.5-10.5は少し暗くする。尺10.5秒）
# 右上PRは台本が削除している。最後の2秒の「広告 #PR」はSRT。
NAME="2026-11-14-ペット-kuroneko-bane"
write_card "$BUILD/bane-1.txt" \
  "カット1　0.0-3.0秒" \
  "ライムのばねの横で黒猫が座って止まっている" \
  "前足は床。ばねは転がらない" \
  "人は映っていない"
write_card "$BUILD/bane-2.txt" \
  "カット2　3.0-6.0秒" \
  "しっぽの先が1回揺れて、ばねから離れたまま止まる" \
  "体と前足は動かない。ばねは転がらない" \
  "人は映っていない"
write_card "$BUILD/bane-3.txt" \
  "カット3　6.0-8.5秒" \
  "無地の器。中に粒。横に文字の無い袋" \
  "黒猫は離れて座っている。手は無い" \
  "商品名は出さない"
write_card "$BUILD/bane-4.txt" \
  "カット3のまま　8.5-10.5秒" \
  "同じ画を少し暗くする" \
  "中央「広告 #PR」" \
  "人は映っていない"
render "$NAME" 10.5 252 228 8.5 \
  0 3 "$BUILD/bane-1.txt" \
  3 6 "$BUILD/bane-2.txt" \
  6 8.5 "$BUILD/bane-3.txt" \
  8.5 - "$BUILD/bane-4.txt"

# ペット マット（台本: 0.0-3.0 / 3.0-6.0 / 6.0-8.5 / 8.5-10.5は少し暗くする。尺10.5秒）
NAME="2026-11-15-ペット-kuroneko-matto"
write_card "$BUILD/mat-1.txt" \
  "カット1　0.0-3.0秒" \
  "ピーチ色のマットの横の床で黒猫が座っている" \
  "マットの上にはいない。前足はマットの外" \
  "人は映っていない"
write_card "$BUILD/mat-2.txt" \
  "カット2　3.0-6.0秒" \
  "耳が1回マットの方へ向いて止まる" \
  "体は起きたまま。マットには乗らない" \
  "人は映っていない"
write_card "$BUILD/mat-3.txt" \
  "カット3　6.0-8.5秒" \
  "無地の器。中に粒。横に文字の無い袋" \
  "黒猫は離れて座っている。手は無い" \
  "商品名は出さない"
write_card "$BUILD/mat-4.txt" \
  "カット3のまま　8.5-10.5秒" \
  "同じ画を少し暗くする" \
  "中央「広告 #PR」" \
  "人は映っていない"
render "$NAME" 10.5 252 228 8.5 \
  0 3 "$BUILD/mat-1.txt" \
  3 6 "$BUILD/mat-2.txt" \
  6 8.5 "$BUILD/mat-3.txt" \
  8.5 - "$BUILD/mat-4.txt"

# 金メモ 加給年金（台本: 0.0-3.0 / 3.0-8.5 / 8.5-10.5。PRなし。尺10.5秒）
# 右の423,700円は3.0まで。配偶者の行は0.5。特別加算は3.0まで出さない。合計の行は5.5まで出さない。
# 画面に出さない円（子の加給、他の生年月日）は出さない。
NAME="2026-11-15-金メモ-kakyu-nenkin"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/kak-right-big.txt" "423,700円"
write_card "$BUILD/kak-right-small.txt" "昭和18年4月2日以後の合計"
write_card "$BUILD/kak-head.txt" "日本年金機構・令和8年4月から"
write_card "$BUILD/kak-row1.txt" \
  "配偶者の加給（65歳未満）" \
  "243,800円"
write_card "$BUILD/kak-row1-note.txt" "大正15年4月1日以前生まれの配偶者は年齢制限なし"
write_card "$BUILD/kak-row2.txt" "受給権者が昭和18年4月2日以後・179,900円"
write_card "$BUILD/kak-row3.txt" \
  "上の2つの合計" \
  "423,700円"
write_card "$BUILD/kak-note.txt" "生計維持。中高齢の特例は概要欄。届出"
write_card "$BUILD/kak-foot.txt" \
  "厚生年金20年以上が基本。中高齢の特例は概要欄" \
  "生計を維持されていること" \
  "届出が要る" \
  "42万3,700円は、昭和18年4月2日以後の受給権者の合計"
write_card "$BUILD/kak-src.txt" "出典：日本年金機構"
write_card "$BUILD/kak-credit.txt" "VOICEVOX:冥鳴ひまり"
add_text "$OV" "$BUILD/kak-right-big.txt" 40 white "w-text_w-80" 640 'lt(t\,3)'
add_text "$OV" "$BUILD/kak-right-small.txt" 26 white "w-text_w-80" 696 'lt(t\,3)'
add_text "$OV" "$BUILD/kak-head.txt" 28 white 40 760 'gte(t\,3)'
add_text "$OV" "$BUILD/kak-row1.txt" 26 white 40 830 'gte(t\,0.5)*lt(t\,3)'
add_text "$OV" "$BUILD/kak-row1.txt" 26 0xBDBDBD 40 830 'gte(t\,3)'
add_text "$OV" "$BUILD/kak-row1-note.txt" 22 0xE6E6E6 40 910 'gte(t\,0.5)'
add_text "$OV" "$BUILD/kak-row2.txt" 26 white 40 980 'gte(t\,3)*lt(t\,5.5)'
add_text "$OV" "$BUILD/kak-row2.txt" 26 0xBDBDBD 40 980 'gte(t\,5.5)'
add_text "$OV" "$BUILD/kak-row3.txt" 26 white 40 1060 'gte(t\,5.5)*lt(t\,8.5)'
add_text "$OV" "$BUILD/kak-row3.txt" 26 0xBDBDBD 40 1060 'gte(t\,8.5)'
add_text "$OV" "$BUILD/kak-note.txt" 26 white 40 1180 'gte(t\,8.5)'
add_text "$OV" "$BUILD/kak-foot.txt" 22 0xE6E6E6 40 1280 'gte(t\,0.5)'
add_text "$OV" "$BUILD/kak-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/kak-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,8.5)'
write_card "$BUILD/kak-1.txt" \
  "カット1　0.0-3.0秒" \
  "無地の印鑑を机に置いて目を丸くする成人" \
  "右に423,700円" \
  "人物は成人だけ。子どもの絵は無い"
write_card "$BUILD/kak-2.txt" \
  "カット2　3.0-8.5秒" \
  "同じ人が左下に小さく、印鑑は机の上" \
  "中央に早見表" \
  "人物は成人だけ。子どもの絵は無い"
write_card "$BUILD/kak-3.txt" \
  "カット3　8.5-10.5秒" \
  "同じ人が印鑑を横に置く。うなずく" \
  "指はささない。表は上に残す" \
  "人物は成人だけ。子どもの絵は無い"
render "$NAME" 10.5 252 228 "" \
  0 3 "$BUILD/kak-1.txt" \
  3 8.5 "$BUILD/kak-2.txt" \
  8.5 - "$BUILD/kak-3.txt"

# 金メモ 高額介護（台本: 0.0-3.0 / 3.0-8.5 / 8.5-10.5。PRなし。尺10.5秒）
# 右の44,400円は3.0まで。1行目は0.5。93,000円は3.0まで出さない。140,100円は5.5まで出さない。
# 年収の約、15,000円、24,600円、82.65万円は画面に出さない。
NAME="2026-11-16-金メモ-kougaku-kaigo"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/kou-right-big.txt" "44,400円"
write_card "$BUILD/kou-right-small.txt" "課税所得380万円未満・世帯"
write_card "$BUILD/kou-head.txt" "厚生労働省・世帯の月額"
write_card "$BUILD/kou-income-note.txt" "年収の約は概要欄"
write_card "$BUILD/kou-row1.txt" \
  "課税所得380万円未満" \
  "44,400円（世帯）"
write_card "$BUILD/kou-row2.txt" \
  "課税所得380万円以上690万円未満" \
  "93,000円（世帯）"
write_card "$BUILD/kou-row3.txt" \
  "課税所得690万円以上" \
  "140,100円（世帯）"
write_card "$BUILD/kou-note.txt" "65歳以上の課税所得で判定。非課税の円は概要欄。申請"
write_card "$BUILD/kou-foot.txt" \
  "世帯は、介護サービスを利用した人全員の負担の合計" \
  "判定は同一世帯内の65歳以上の課税所得" \
  "食費・居住費・福祉用具購入費等の一部は、この月額に足さない、とページにある" \
  "非課税の円は概要欄"
write_card "$BUILD/kou-src.txt" "出典：厚生労働省"
write_card "$BUILD/kou-credit.txt" "VOICEVOX:冥鳴ひまり"
add_text "$OV" "$BUILD/kou-right-big.txt" 40 white "w-text_w-80" 640 'lt(t\,3)'
add_text "$OV" "$BUILD/kou-right-small.txt" 26 white "w-text_w-80" 696 'lt(t\,3)'
add_text "$OV" "$BUILD/kou-head.txt" 28 white 40 760 'gte(t\,3)'
add_text "$OV" "$BUILD/kou-income-note.txt" 22 0xE6E6E6 40 810 'gte(t\,3)'
add_text "$OV" "$BUILD/kou-row1.txt" 26 white 40 860 'gte(t\,0.5)*lt(t\,3)'
add_text "$OV" "$BUILD/kou-row1.txt" 26 0xBDBDBD 40 860 'gte(t\,3)'
add_text "$OV" "$BUILD/kou-row2.txt" 26 white 40 980 'gte(t\,3)*lt(t\,5.5)'
add_text "$OV" "$BUILD/kou-row2.txt" 26 0xBDBDBD 40 980 'gte(t\,5.5)'
add_text "$OV" "$BUILD/kou-row3.txt" 26 white 40 1120 'gte(t\,5.5)*lt(t\,8.5)'
add_text "$OV" "$BUILD/kou-row3.txt" 26 0xBDBDBD 40 1120 'gte(t\,8.5)'
add_text "$OV" "$BUILD/kou-note.txt" 26 white 40 1260 'gte(t\,8.5)'
add_text "$OV" "$BUILD/kou-foot.txt" 22 0xE6E6E6 40 1360 'gte(t\,0.5)'
add_text "$OV" "$BUILD/kou-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/kou-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,8.5)'
write_card "$BUILD/kou-1.txt" \
  "カット1　0.0-3.0秒" \
  "大人の室内履き1足を見て目を丸くする成人" \
  "右に44,400円" \
  "人物は成人だけ。子どもの絵は無い"
write_card "$BUILD/kou-2.txt" \
  "カット2　3.0-8.5秒" \
  "同じ人が左下に小さく、室内履きは床に1足" \
  "中央に早見表" \
  "人物は成人だけ。子どもの絵は無い"
write_card "$BUILD/kou-3.txt" \
  "カット3　8.5-10.5秒" \
  "同じ人が室内履きの横でうなずく" \
  "指はささない。表は上に残す" \
  "人物は成人だけ。子どもの絵は無い"
render "$NAME" 10.5 252 228 "" \
  0 3 "$BUILD/kou-1.txt" \
  3 8.5 "$BUILD/kou-2.txt" \
  8.5 - "$BUILD/kou-3.txt"

# 金メモ 技能習得手当（台本: 0.0-3.0 / 3.0-8.5 / 8.5-10.5。PRなし。尺10.5秒）
# 右の42,500円は3.0まで。通所の行は0.5。500円と20,000円は3.0まで出さない。10,700円は5.5まで出さない。
# 日数に日額を掛けた円は出さない。学生・制服は出さない。
NAME="2026-11-17-金メモ-ginou-shutoku"
OV="$BUILD/${NAME}.overlay"
: > "$OV"
write_card "$BUILD/gin-right-big.txt" "42,500円"
write_card "$BUILD/gin-right-small.txt" "通所手当の月額の上限"
write_card "$BUILD/gin-head.txt" "ハローワーク・基本手当とは別"
write_card "$BUILD/gin-row1.txt" \
  "通所手当" \
  "月額最高42,500円"
write_card "$BUILD/gin-row2.txt" \
  "受講手当" \
  "日額500円・上限20,000円"
write_card "$BUILD/gin-row3.txt" \
  "寄宿手当" \
  "月額10,700円"
write_card "$BUILD/gin-note.txt" "公共職業安定所長または地方運輸局長の指示。対象外の日は日割"
write_card "$BUILD/gin-foot.txt" \
  "公共職業安定所長または地方運輸局長の指示で公共職業訓練等を受けるとき" \
  "基本手当とは別" \
  "通所と寄宿は、支給対象にならない日がある月は日割で減額、とページにある"
write_card "$BUILD/gin-src.txt" "出典：ハローワーク"
write_card "$BUILD/gin-credit.txt" "VOICEVOX:冥鳴ひまり"
add_text "$OV" "$BUILD/gin-right-big.txt" 40 white "w-text_w-80" 640 'lt(t\,3)'
add_text "$OV" "$BUILD/gin-right-small.txt" 26 white "w-text_w-80" 696 'lt(t\,3)'
add_text "$OV" "$BUILD/gin-head.txt" 28 white 40 760 'gte(t\,3)'
add_text "$OV" "$BUILD/gin-row1.txt" 26 white 40 860 'gte(t\,0.5)*lt(t\,3)'
add_text "$OV" "$BUILD/gin-row1.txt" 26 0xBDBDBD 40 860 'gte(t\,3)'
add_text "$OV" "$BUILD/gin-row2.txt" 26 white 40 980 'gte(t\,3)*lt(t\,5.5)'
add_text "$OV" "$BUILD/gin-row2.txt" 26 0xBDBDBD 40 980 'gte(t\,5.5)'
add_text "$OV" "$BUILD/gin-row3.txt" 26 white 40 1100 'gte(t\,5.5)*lt(t\,8.5)'
add_text "$OV" "$BUILD/gin-row3.txt" 26 0xBDBDBD 40 1100 'gte(t\,8.5)'
add_text "$OV" "$BUILD/gin-note.txt" 26 white 40 1220 'gte(t\,8.5)'
add_text "$OV" "$BUILD/gin-foot.txt" 22 0xE6E6E6 40 1320 'gte(t\,0.5)'
add_text "$OV" "$BUILD/gin-credit.txt" 24 white 40 1848 'gte(t\,0)'
add_text "$OV" "$BUILD/gin-src.txt" 24 white "w-text_w-40" 1848 'gte(t\,8.5)'
write_card "$BUILD/gin-1.txt" \
  "カット1　0.0-3.0秒" \
  "無地の水筒を持って目を丸くする成人" \
  "右に42,500円" \
  "人物は成人だけ。学生も制服も無い"
write_card "$BUILD/gin-2.txt" \
  "カット2　3.0-8.5秒" \
  "同じ人が左下に小さく、水筒を机に置く" \
  "中央に早見表" \
  "人物は成人だけ。学生も制服も無い"
write_card "$BUILD/gin-3.txt" \
  "カット3　8.5-10.5秒" \
  "同じ人が水筒を横に置く。うなずく" \
  "指はささない。表は上に残す" \
  "人物は成人だけ。学生も制服も無い"
render "$NAME" 10.5 252 228 "" \
  0 3 "$BUILD/gin-1.txt" \
  3 8.5 "$BUILD/gin-2.txt" \
  8.5 - "$BUILD/gin-3.txt"

# ペット 給餌箱（台本: 0.0-3.0 / 3.0-6.0 / 6.0-8.5 / 8.5-10.5は少し暗くする。尺10.5秒）
# 日付の順では金メモの11/16より前だが、上の金メモと関数の並びの都合で最後に書く。秒は台本どおり。
NAME="2026-11-16-ペット-kuroneko-kyujiki"
write_card "$BUILD/kyu-1.txt" \
  "カット1　0.0-3.0秒" \
  "白い箱の横で黒猫が座って止まっている" \
  "出し口は閉まっている。顔は外。口は閉じている" \
  "人は映っていない"
write_card "$BUILD/kyu-2.txt" \
  "カット2　3.0-6.0秒" \
  "視線だけが丸い出し口へ1回向く" \
  "口は閉じている。前足は床。出し口は閉まったまま" \
  "人は映っていない"
write_card "$BUILD/kyu-3.txt" \
  "カット3　6.0-8.5秒" \
  "無地の器。中に粒。横に文字の無い袋" \
  "黒猫は離れて座っている。手は無い" \
  "商品名は出さない"
write_card "$BUILD/kyu-4.txt" \
  "カット3のまま　8.5-10.5秒" \
  "同じ画を少し暗くする" \
  "中央「広告 #PR」" \
  "人は映っていない"
render "$NAME" 10.5 252 228 8.5 \
  0 3 "$BUILD/kyu-1.txt" \
  3 6 "$BUILD/kyu-2.txt" \
  6 8.5 "$BUILD/kyu-3.txt" \
  8.5 - "$BUILD/kyu-4.txt"

echo "完了"
