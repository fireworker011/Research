# いらすとやスカッとショート

縦9:16、25〜40秒、12〜14シーン。いらすとやのキャラが口パクして、テロップと効果音が入るショートを、編集ソフトなしで書き出す。

手順の元は、いらすとや素材のキャラを動かし、背景はコードで描き、VOICEVOX で話者を分け、波形から口の開きを計算して、6秒ずつ書き出して結合する、という流れ。

投稿はしない。このツールは mp4 をローカルに出すだけ。

## 入力

ネタの箇条書き、オチ、任意で参考動画のスクショ5〜10枚。

```json
{
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

`hook` は冒頭2秒で見せる結末。`punchline` は反撃で、空だと止まる。`「」` は登場人物のセリフになる。

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

1. フック→展開→オチ→締め、の14シーン。テロップの改行位置まで決める
2. いらすとやを検索してダウンロードする。文字が焼き込まれた絵、季節もの、2人組は弾く。背景（オフィス、夜、集中線、チャット画面）はコードで描く。1本20点まで、目安は9〜10点
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
