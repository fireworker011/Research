# いらすとやスカッとショート

縦9:16、25〜40秒。台本は実測した短い回の5ビート（フック、状況、一文、対立、オチ）に、VOICEVOX のクレジットを足した6シーン。いらすとやのキャラが口パクして、テロップと効果音が入るショートを、編集ソフトなしで書き出す。秒の根拠は `research/script-kata/`。

手順の元は、いらすとや素材のキャラを動かし、背景はコードで描き、VOICEVOX で話者を分け、波形から口の開きを計算して、6秒ずつ書き出して結合する、という流れ。

投稿はしない。このツールは mp4 をローカルに出すだけ。

## 入力

ネタの箇条書き、オチ、任意で参考動画のスクショ5〜10枚。

```json
{
  "hook": "奢らせ同僚に会計を置いて帰った話",
  "series_character": "奢らせ同僚",
  "bullets": [
    "飲み会の最後、10人分の伝票が俺の前に置かれた「会計はお前が出して」",
    "終電だ",
    "一言残して店を出た"
  ],
  "punchline": "翌朝、頭を下げて全額を振り込んできた",
  "closing": ""
}
```

箇条書きは3つ。1つ目が状況、2つ目が黒地の一文、3つ目以降が対立（4つ目以降は対立シーンに続ける）。最初の `「」` が冒頭の相手のせりふになる。`punchline` が空だと止まる。`closing` は台本JSONに残るだけで、読み上げない。短い回の実測に、動画内の問いかけが無いため。

各ビートの秒の目安は 2.37 / 5.53 / 0.97 / 5.53 / 11.05（@junjun_ranran の 25.45秒の回）。音声が長いと伸び、全体が40秒を超えると速度を上げて収める。クレジットは実測のビートではなく、使った声の表示で、約2秒。

スクショがあるときは `--screenshots フォルダ` を付ける。冒頭、展開、オチの直前、オチ、締め、の5〜10枚。テロップの高さとキャラの左右をそこに寄せる。無くても、下に太いテロップ、中央にキャラ、という形で作る。

## 準備

```bash
cd tools/irasutoya-short
pip install -r requirements.txt
```

日本語フォント（WenQuanYi Micro Hei か Noto Sans CJK）と ffmpeg が要る。文字入り素材を弾くときは tesseract（`jpn`）もあるとよい。

ナレーションは VOICEVOX core 0.16 系。Linux x64 の例:

```bash
pip install "https://github.com/VOICEVOX/voicevox_core/releases/download/0.16.4/voicevox_core-0.16.4-cp310-abi3-manylinux_2_34_x86_64.whl"

mkdir -p "$HOME/.cache/irasutoya-short"
curl -fsSL -o /tmp/vvx-download "https://github.com/VOICEVOX/voicevox_core/releases/download/0.16.4/download-linux-x64"
chmod +x /tmp/vvx-download
# 規約に同意する場合だけ y を渡す。モデルは 0（めたん他）・4（玄野武宏・剣崎雌雄）・9（白上虎太郎）
printf 'y\n' | PAGER=cat /tmp/vvx-download --exclude c-api --exclude additional-libraries \
  --models-pattern '0.vvm' -o "$HOME/.cache/irasutoya-short/voicevox"
printf 'y\n' | PAGER=cat /tmp/vvx-download --only models --models-pattern '4.vvm' \
  -o "$HOME/.cache/irasutoya-short/voicevox"
printf 'y\n' | PAGER=cat /tmp/vvx-download --only models --models-pattern '9.vvm' \
  -o "$HOME/.cache/irasutoya-short/voicevox"

PYTHONPATH=. python -m irasutoya_short doctor
```

他の OS は [voicevox_core 0.16.4](https://github.com/VOICEVOX/voicevox_core/releases/tag/0.16.4) の wheel と downloader を同じ配置にする。置き場所を変えるときは `IRASUTOYA_VOICEVOX`。

声の割り当て:

| 役 | 声 | クレジット |
| --- | --- | --- |
| ナレーション | 四国めたん | VOICEVOX:四国めたん |
| 主人公 | 白上虎太郎 | VOICEVOX:白上虎太郎 |
| 仕事押し付け君 | 玄野武宏 | VOICEVOX:玄野武宏 |
| 上司 | 剣崎雌雄 | VOICEVOX:剣崎雌雄 |

青山龍星は使わない。個人事業や法人だと、クレジットがあっても事前許可が要るため。

## 作る

```bash
cd tools/irasutoya-short
PYTHONPATH=. python -m irasutoya_short make examples/oshitsuke.json \
  --work work/oshitsuke \
  --out work/oshitsuke/out.mp4 \
  --screenshots /path/to/shots
```

やっていること:

1. フック→状況→一文→対立→オチ、の5シーンにクレジットを足す。テロップの改行位置まで決める。型は `research/script-kata/irasutoya-sukatto.md`
2. いらすとやを検索してダウンロードする。文字が焼き込まれた絵、季節もの、2人組は弾く。背景（オフィス、夜、集中線、チャット画面）はコードで描く。1本20点まで。この型で使うキャラは4点
3. 話者ごとに合成音声
4. 波形から1コマごとの口の開き
5. 効果音をその場で合成。BGM は任意（`--no-bgm` で無し）。どちらもオリジナルなのでクレジット不要
6. ズーム、揺れ、集中線、テロップを乗せて6秒ごとに書き出し、結合して mp4

`work/` に台本 `project.json`、採用と不採用の素材、プレビュー PNG、`REPORT.json` が残る。いらすとやの画像はリポジトリに入れない。

## 口語で直す

専門用語は要らない。作業フォルダを渡して、気になったことだけ言う。

```bash
PYTHONPATH=. python -m irasutoya_short revise work/oshitsuke "テンポ悪いな" --out work/oshitsuke/out.mp4
PYTHONPATH=. python -m irasutoya_short revise work/oshitsuke "文字がはみ出てる" --out work/oshitsuke/out.mp4
PYTHONPATH=. python -m irasutoya_short revise work/oshitsuke "SEがうるさい" --out work/oshitsuke/out.mp4
PYTHONPATH=. python -m irasutoya_short revise work/oshitsuke "このセリフはナレーションのはず" --out work/oshitsuke/out.mp4
```

| 言い方 | 動き |
| --- | --- |
| テンポ悪い、長い | 音声を速くして取り直す |
| 早すぎ | 遅くする |
| 文字がはみ出てる | テロップを縮小 |
| 文字が小さい | テロップを拡大 |
| SEがうるさい、声が小さい | 効果音（とBGM）を下げる |
| 口が動かない | 口の開きを大きくする |
| 地の文とセリフが一緒 | シーンを分ける |
| 揺れがうるさい | 揺れを消す |

## クレジットと点数

動画の最後に、使った VOICEVOX の名前を出している。概要欄に書く場合も同じ文字列。

いらすとやはクレジット不要。1制作物20点までが商用無料で、同じ絵の使い回しは1点。21点以上の商用は有償。素材自体の再配布や、イラストが主体の商品化はできない。公開前に [ご利用について](https://www.irasutoya.com/p/terms.html) と [よくあるご質問](https://www.irasutoya.com/p/faq.html) を見る。

効果音とBGMは合成したオリジナル。手元の音源を足す機能は無いので、後から音を載せるときはその音源の規約に従う。

## テスト

```bash
cd tools/irasutoya-short
PYTHONPATH=. python -m unittest tests.test_core
```
