# Grok Build で1本書く

空の Linux から、いらすとや型ショートを1本、ローカルの mp4 にする手順。このファイルだけで進める。

投稿はしない。YouTube にも X にも上げない。mp4 は作業フォルダに残す。

## 前提

- Linux x86_64（Grok Build）
- Python 3.10 以上
- ネット。いらすとやの検索と、VOICEVOX の取得に使う

他の OS で VOICEVOX を置くときは、手順3の wheel と downloader を [voicevox_core 0.16.4](https://github.com/VOICEVOX/voicevox_core/releases/tag/0.16.4) のその OS 用に替える。置き場所は同じ。

## 1. パッケージ

```bash
sudo apt-get update
sudo apt-get install -y \
  python3 \
  python3-pip \
  python3-venv \
  ffmpeg \
  fonts-wqy-microhei \
  tesseract-ocr \
  tesseract-ocr-jpn \
  curl \
  ca-certificates
```

tesseract の `jpn` は、文字が焼き込まれたいらすとやを落とすために使う。入っていなくても書き出しは進む。その場合、文字入りの絵を落としにくくなる。

## 2. Python

リポジトリのルートを、手元のパスに読み替える。

```bash
cd /path/to/Research/tools/irasutoya-short
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

`requirements.txt` は Pillow と NumPy。

## 3. VOICEVOX

使う声は4つだけ。

| 役 | 声 | モデル | クレジット |
| --- | --- | --- | --- |
| ナレーション | 四国めたん | `0.vvm` | VOICEVOX:四国めたん |
| 主人公 | 白上虎太郎 | `9.vvm` | VOICEVOX:白上虎太郎 |
| 仕事押し付け君 | 玄野武宏 | `4.vvm` | VOICEVOX:玄野武宏 |
| 上司 | 剣崎雌雄 | `4.vvm` | VOICEVOX:剣崎雌雄 |

青山龍星は入れない。個人事業や法人だと、クレジットがあっても事前許可が要る。

`printf 'y'` は VOICEVOX の利用規約に同意する、という意味。同意しないなら、ここで止める。

```bash
python -m pip install "https://github.com/VOICEVOX/voicevox_core/releases/download/0.16.4/voicevox_core-0.16.4-cp310-abi3-manylinux_2_34_x86_64.whl"

mkdir -p "$HOME/.cache/irasutoya-short"
curl -fsSL -o /tmp/vvx-download "https://github.com/VOICEVOX/voicevox_core/releases/download/0.16.4/download-linux-x64"
chmod +x /tmp/vvx-download
printf 'y\n' | PAGER=cat /tmp/vvx-download --exclude c-api --exclude additional-libraries \
  --models-pattern '0.vvm' -o "$HOME/.cache/irasutoya-short/voicevox"
printf 'y\n' | PAGER=cat /tmp/vvx-download --only models --models-pattern '4.vvm' \
  -o "$HOME/.cache/irasutoya-short/voicevox"
printf 'y\n' | PAGER=cat /tmp/vvx-download --only models --models-pattern '9.vvm' \
  -o "$HOME/.cache/irasutoya-short/voicevox"
```

置き場所を変えるときは、以降のコマンドの前に付ける。

```bash
export IRASUTOYA_VOICEVOX="$HOME/.cache/irasutoya-short/voicevox"
```

いらすとや画像のキャッシュを変えるときは `IRASUTOYA_CACHE`。既定は `$HOME/.cache/irasutoya-short/images`。

## 4. 書き出す前の確認

`tools/irasutoya-short` で、仮想環境を有効にしたまま。

```bash
PYTHONPATH=. python -m irasutoya_short doctor
PYTHONPATH=. python -m irasutoya_short templates
PYTHONPATH=. python -m unittest tests.test_core
```

`doctor` は次の3行が出れば足りる。

```text
voicevox: ok
ffmpeg: ok
font: /usr/share/fonts/truetype/wqy/wqy-microhei.ttc
```

`voicevox: missing` のまま `make` しない。`ffmpeg: missing` や `font: missing` も、手順1に戻る。テストはネットも合成音声も使わない。

## 5. ネタ

`examples/oshitsuke.json` をコピーして、`template` だけ変えてよい。中身の箇条書きを空にすると止まる。`punchline` も空だと止まる。

```json
{
  "template": "ranking",
  "hook": "仕事押し付け君を請求書で撃退した話",
  "series_character": "仕事押し付け君",
  "bullets": [
    "金曜の17時、終わってない企画書が俺の机に置かれた",
    "そう言い残して定時で帰っていった「お前の方が早いだろ」",
    "誰もいないオフィスで終電まで3時間かかった",
    "月曜の朝、何事もなかった顔だった"
  ],
  "punchline": "作業ログと請求書を社内チャットに全体送信した。その場で送金して全員の前で頭を下げた",
  "closing": "あなたならどうする？"
}
```

`「」` は登場人物のセリフになる。

| template | 画面の進み方 |
| --- | --- |
| `sukatto` | フック→展開→オチ→締め。黄色の丸いテロップ。フックだけ速い |
| `before_after` | 先に結果、それからビフォー、転換、アフター。青の角帯から橙の帯へ。ビフォーは遅く、アフターは速い |
| `aruaru` | あるあるを短く並べて、最後に一番。ピンクの pill。項目ごとに小さいクリック |
| `ranking` | 第3位、第2位、第1位。金の角帯。1位だけ間を置く |
| `qa` | 問い、外れ、答え。問いは黄色で間を置き、答えは緑で速い |

## 6. 1本書く

```bash
PYTHONPATH=. python -m irasutoya_short make examples/oshitsuke.json \
  --template ranking \
  --work work/ranking \
  --out work/ranking/out.mp4 \
  --no-bgm
```

`--template` を付けると、JSON の `template` よりこちらが勝つ。BGM も載せるときは `--no-bgm` を外す。参考スクショがあるときは `--screenshots フォルダ` を足す。5〜10枚。テロップの高さとキャラの左右を、その画像に寄せる。

このコマンドがすること:

1. テンプレで 12〜14 シーンの台本を作る
2. いらすとやを検索して、条件に合う絵だけ保存する。文字入り、季節もの、2人組、白衣、検索語がタイトルに無い絵は捨てる。1本20点まで。同じ絵の使い回しは1点。背景はコードで描くので点数に入らない
3. 話した声だけ、VOICEVOX で読む。テンプレごとに速さと間が違う
4. 波形から口の開きを計算し、顔の中の口の線に描く。あごの影や襟には置かない。体ごと上下には動かさない
5. 効果音はコードで合成する。クレジットは要らない
6. フレームを ffmpeg に流して、1本の mp4 にする。6秒ごとに切って繋がないので、つなぎ目で音が飛ばない

検索とエンコードで待つ。所要はマシンによるので、ここには時間を書かない。

いらすとやの画像は `work/` とキャッシュにだけ置く。リポジトリには入れない。

## 7. できたものの見方

- 動画: `work/ranking/out.mp4`
- 台本と設定: `work/ranking/project.json`
- 要約: `work/ranking/REPORT.json`
- 口の位置の赤点: `work/ranking/assets/debug_mouth/`
- シーンの静止画: `work/ranking/preview/`

`REPORT.json` で見るもの:

- `asset_count` が 20 以下
- `credits` に、その回で話した `VOICEVOX:` の名前がある
- `within_20_30` が true

動画の最後のクレジットは消さない。概要欄に書くときも、同じ文字列を使う。

画面サイズの確認:

```bash
ffprobe -v error -show_entries stream=width,height,codec_name -of default work/ranking/out.mp4
```

幅 1080、高さ 1920。尺の秒数は `REPORT.json` の `duration_sec`。

## 8. 口語で直す

書き直しもローカルだけ。投稿はしない。

```bash
PYTHONPATH=. python -m irasutoya_short revise work/ranking "テンポ悪いな" --out work/ranking/out.mp4
PYTHONPATH=. python -m irasutoya_short revise work/ranking "文字がはみ出てる" --out work/ranking/out.mp4
PYTHONPATH=. python -m irasutoya_short revise work/ranking "SEがうるさい" --out work/ranking/out.mp4
```

テンポの指示は、そのテンプレの役ごとの速さも一緒に動かす。

## 9. 止まったとき

| 表示 | 戻る場所 |
| --- | --- |
| `voicevox: missing`、または「VOICEVOX の Python パッケージがありません」「VOICEVOX の実行ファイルがありません」 | 手順3。wheel と、`0.vvm` `4.vvm` `9.vvm` |
| `ffmpeg がありません` | 手順1の `ffmpeg` |
| `font: missing` | 手順1の `fonts-wqy-microhei` |
| 「適切ないらすとやが見つかりませんでした」 | 通信。キャッシュを捨てて取り直すなら `rm -rf "$HOME/.cache/irasutoya-short/images"` |
| 「未知のテンプレです」 | `python -m irasutoya_short templates` の id を使う |
| `ffmpeg が失敗しました` | メッセージの ffmpeg の行を見る。ディスク不足か、手順1の ffmpeg が入っていないことが多い |

## 規約

- いらすとやは1制作物20点まで商用無料。同じ絵の重複は1点。21点以上の商用は有償。クレジット表記は不要。素材そのものの再配布や、イラストを主体にした商品化は不可。公開前に [ご利用について](https://www.irasutoya.com/p/terms.html) と [よくあるご質問](https://www.irasutoya.com/p/faq.html) を見る
- VOICEVOX は、動画の最後に出ている名前を残す。青山龍星は使わない
- 効果音と BGM はこのツールが合成したオリジナル。後から別の音を載せるときは、その音源の規約に従う
