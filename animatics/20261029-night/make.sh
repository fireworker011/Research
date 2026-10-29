#!/usr/bin/env bash
# 下書き動画（灰色の静止カード＋SRT焼き込み）。音は入れない。絵は描かない。生成AIは使わない。
# 字幕は同じフォルダの subs/（焼き込む時刻まで入れたもの）。台本ファイルはコミットしない。
# 使い方: bash animatics/20261029-night/make.sh
#
# カードの秒は台本のカットどおり。字幕の文言は変えない。
# カットより先に出ていた字幕の開始だけ、subs/ 側でカットの境目へ寄せてある。
# ffmpeg が SRT を ASS にすると PlayRes が 384x288 になり、9:16 では字が縦に伸びる。
# 直すのは PlayRes と字体だけ（1080x1920、文泉驛微米黑、画面上で約40px）。
# 金メモの SRT には位置タグが無いので、焼き込み時だけ位置を足す（文言と時刻はそのまま）。
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
BUILD=${BUILD:-/tmp/animatic-build-20261029-night}
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

# SRTをASSにし、画面サイズだけ合わせる。ペットと婚活はイベント行を触らない。
to_ass() {
  local src="$1" dst="$2"
  ffmpeg -y -hide_banner -loglevel error -i "$src" "$dst"
  sed -i \
    -e 's/^PlayResX:.*/PlayResX: 1080/' \
    -e 's/^PlayResY:.*/PlayResY: 1920/' \
    -e 's/^Style: Default,.*/Style: Default,WenQuanYi Micro Hei,40,\&H00FFFFFF,\&H000000FF,\&H00000000,\&H00000000,0,0,0,0,100,100,0,0,1,3,0,2,60,60,90,1/' \
    "$dst"
}

# 金メモだけ。位置タグが無いので、問いを上、台詞を下、出典をいちばん下に分ける。文言と時刻は変えない。
place_izoku() {
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
    if "出典" in body:
        parts[7] = "36"
        parts[9] = "{\\an2\\fs26}" + body
    elif body.startswith("子ども2人なら"):
        parts[7] = "70"
        parts[9] = "{\\an8}" + body
    else:
        parts[7] = "150"
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
  if [[ "$name" == *izoku-nenkin ]]; then
    place_izoku "$ass"
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
drawtext=fontfile=${FONT}:textfile=${textfile}:fontsize=36:fontcolor=0xF5D76E:borderw=2:bordercolor=0x222222:x=(w-text_w)/2:y=430:line_spacing=8:enable='${enable}',
EOF
  done
  if [[ "$name" == *izoku-nenkin ]]; then
    cat >> "$filter" << EOF
drawtext=fontfile=${FONT}:textfile=${BUILD}/izoku-amount.txt:fontsize=42:fontcolor=white:borderw=3:bordercolor=0x222222:x=w-text_w-80:y=980:line_spacing=12:enable='lt(t\\,2.5)',
EOF
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

# ペット キャリー（台本: カット1 0.0-3.6 / 2 3.6-7.2 / 3 7.2-10.4 / 4 10.4-13.0、13.0-15.0はカット4を少し暗くする。尺15.0秒）
write_card "$BUILD/carrier-1.txt" \
  "カット1　0.0-3.6秒" \
  "開いたキャリーの入口" \
  "黒猫が顔だけ出して止まっている" \
  "まばたき1回。人は映っていない"
write_card "$BUILD/carrier-2.txt" \
  "カット2　3.6-7.2秒" \
  "同じ画角。白い器のウェットごはん" \
  "袖と手が粒をのせて出ていく" \
  "顔は映っていない"
write_card "$BUILD/carrier-3.txt" \
  "カット3　7.2-10.4秒" \
  "同じ画角。手は出ていった後" \
  "粒ののったごはんの奥" \
  "黒猫はまだキャリーの中"
write_card "$BUILD/carrier-4.txt" \
  "カット4　10.4-13.0秒" \
  "同じ画角" \
  "黒猫がキャリーから出て" \
  "器に顔を入れて食べている"
write_card "$BUILD/carrier-5.txt" \
  "カット4のまま　13.0-15.0秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上のPRは残す"
render "2026-11-02-ペット-kuroneko-carrier" 15 360 336 13 \
  0 3.6 "$BUILD/carrier-1.txt" \
  3.6 7.2 "$BUILD/carrier-2.txt" \
  7.2 10.4 "$BUILD/carrier-3.txt" \
  10.4 13 "$BUILD/carrier-4.txt" \
  13 - "$BUILD/carrier-5.txt"

# ペット 粒（台本: 0.0-3.6 / 3.6-7.4 / 7.4-10.4 / 10.4-13.0、13.0-15.0はカット4を少し暗くする。尺15.0秒）
write_card "$BUILD/tsubu-1.txt" \
  "カット1　0.0-3.6秒" \
  "小皿の粒に鼻を近づける黒猫" \
  "ひげが1回動く" \
  "人は映っていない"
write_card "$BUILD/tsubu-2.txt" \
  "カット2　3.6-7.4秒" \
  "同じ画角" \
  "粒をくわえて顔を上げ" \
  "口を閉じて食べる"
write_card "$BUILD/tsubu-3.txt" \
  "カット3　7.4-10.4秒" \
  "同じ画角" \
  "空いた小皿の前で" \
  "黒猫が座り直す"
write_card "$BUILD/tsubu-4.txt" \
  "カット4　10.4-13.0秒" \
  "同じ画角" \
  "空いた小皿の横で" \
  "口のまわりを1回なめる"
write_card "$BUILD/tsubu-5.txt" \
  "カット4のまま　13.0-15.0秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上のPRは残す"
render "2026-11-03-ペット-kuroneko-tsubu" 15 360 336 13 \
  0 3.6 "$BUILD/tsubu-1.txt" \
  3.6 7.4 "$BUILD/tsubu-2.txt" \
  7.4 10.4 "$BUILD/tsubu-3.txt" \
  10.4 13 "$BUILD/tsubu-4.txt" \
  13 - "$BUILD/tsubu-5.txt"

# ペット 棚（台本: 0.0-3.6 / 3.6-7.4 / 7.4-10.4 / 10.4-13.0、13.0-15.0は少し暗くする。尺15.0秒）
write_card "$BUILD/tana-1.txt" \
  "カット1　0.0-3.6秒" \
  "低い棚の奥の袋" \
  "床の黒猫が見上げて止まっている" \
  "耳が1回動く。人は映っていない"
write_card "$BUILD/tana-2.txt" \
  "カット2　3.6-7.4秒" \
  "同じ画角" \
  "袖と手が奥の袋を取り" \
  "カリカリの容器の隣に置いて出ていく"
write_card "$BUILD/tana-3.txt" \
  "カット3　7.4-10.4秒" \
  "同じ画角" \
  "容器と袋が並んだ棚" \
  "黒猫は見上げたまま"
write_card "$BUILD/tana-4.txt" \
  "カット4　10.4-13.0秒" \
  "同じ画角" \
  "並んだ棚の下で" \
  "黒猫がまばたきを1回する"
write_card "$BUILD/tana-5.txt" \
  "カット4のまま　13.0-15.0秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上のPRは残す"
render "2026-11-04-ペット-kuroneko-tana" 15 360 336 13 \
  0 3.6 "$BUILD/tana-1.txt" \
  3.6 7.4 "$BUILD/tana-2.txt" \
  7.4 10.4 "$BUILD/tana-3.txt" \
  10.4 13 "$BUILD/tana-4.txt" \
  13 - "$BUILD/tana-5.txt"

# 婚活 頼める人（台本: 0.0-3.0 / 3.0-7.4 / 7.4-13.0、13.0-15.0はカット3を少し暗くする。尺15.0秒）
write_card "$BUILD/tanomeru-1.txt" \
  "カット1　0.0-3.0秒" \
  "公園のベンチ" \
  "三脚に立てたスマホ1台" \
  "画面は空っぽの芝生。人は映っていない"
write_card "$BUILD/tanomeru-2.txt" \
  "カット2　3.0-7.4秒" \
  "同じ公園。手前は両手とカメラ" \
  "肩ごし。顔は映っていない" \
  "奥にニットの女性の後ろ姿"
write_card "$BUILD/tanomeru-3.txt" \
  "カット3　7.4-13.0秒" \
  "カメラの背面モニターに寄る" \
  "木漏れ日の女性の後ろ姿の写真" \
  "持っているのは手だけ"
write_card "$BUILD/tanomeru-4.txt" \
  "カット3のまま　13.0-15.0秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上のPRは残す"
render "2026-11-03-婚活-tanomeru-hito" 15 360 336 13 \
  0 3 "$BUILD/tanomeru-1.txt" \
  3 7.4 "$BUILD/tanomeru-2.txt" \
  7.4 13 "$BUILD/tanomeru-3.txt" \
  13 - "$BUILD/tanomeru-4.txt"

# 婚活 実家のポスト（台本: 0.0-3.0 / 3.0-7.4 / 7.4-10.4 / 10.4-13.0、13.0-15.0はカット4を少し暗くする。尺15.0秒）
write_card "$BUILD/jikka-1.txt" \
  "カット1　0.0-3.0秒" \
  "夕方の門柱" \
  "銀色のポストに郵便がはみ出している" \
  "文字は読めない。人は映っていない"
write_card "$BUILD/jikka-2.txt" \
  "カット2　3.0-7.4秒" \
  "夜の部屋。布団の中" \
  "手がスマホを持つ。顔は映っていない" \
  "画面はパンフの見開き。文字なし"
write_card "$BUILD/jikka-3.txt" \
  "カット3　7.4-10.4秒" \
  "翌朝の同じポスト" \
  "白い無地の封筒が1通" \
  "差出人の文字なし"
write_card "$BUILD/jikka-4.txt" \
  "カット4　10.4-13.0秒" \
  "カット2と同じ布団の中のスマホ" \
  "画面のパンフが別の1社に変わる" \
  "文字なし。顔は映っていない"
write_card "$BUILD/jikka-5.txt" \
  "カット4のまま　13.0-15.0秒" \
  "少し暗い" \
  "中央「広告 #PR」" \
  "右上のPRは残す"
render "2026-11-04-婚活-jikka-post" 15 360 336 13 \
  0 3 "$BUILD/jikka-1.txt" \
  3 7.4 "$BUILD/jikka-2.txt" \
  7.4 10.4 "$BUILD/jikka-3.txt" \
  10.4 13 "$BUILD/jikka-4.txt" \
  13 - "$BUILD/jikka-5.txt"

# 金メモ 遺族基礎年金（台本: 0.0-3.0 / 3.0-10.0 / 10.0-15.0。PRなし。尺15.0秒）
# 1秒目は食卓に茶碗2つ。金額は台本の画面文字（0.0-2.5）。人物は成人。子どもは映さない。
write_card "$BUILD/izoku-1.txt" \
  "カット1　0.0-3.0秒" \
  "食卓の静止画。茶碗が2つ" \
  "成人が文字の無い封筒を持って止まる" \
  "右側に金額。人物は成人だけ"
write_card "$BUILD/izoku-2.txt" \
  "カット2　3.0-10.0秒" \
  "同じ成人が封筒を机に置く" \
  "上は人数の早見表" \
  "人物は成人だけ"
write_card "$BUILD/izoku-3.txt" \
  "カット3　10.0-15.0秒" \
  "同じ成人が茶碗2つを並べ直す" \
  "静かに座る" \
  "人物は成人だけ"
write_card "$BUILD/izoku-amount.txt" \
  "子2人 → 1,334,900円" \
  "年額・計算額"
render "2026-11-02-金メモ-izoku-nenkin" 15 360 336 "" \
  0 3 "$BUILD/izoku-1.txt" \
  3 10 "$BUILD/izoku-2.txt" \
  10 - "$BUILD/izoku-3.txt"

echo "完了"
