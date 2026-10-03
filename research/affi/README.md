# 共通点レポートの置き場所

正本は `research/affi/commonalities.yaml`（schema `affi-commonalities/v1`）。

ジャンルは `beauty_skincare`（美容スキンケア）、`pet_food`（ペットフード）、`pet_camera`（見守りカメラ）。プラットフォームは `youtube` / `tiktok` / `instagram`。9セルすべてを置く。無い調査はキーを消さず、値を `不明` にする。件数を 50 に繰り上げない。

`pattern_id` が `introduce` / `buy_before` / `missing_on_camera` のときだけ、2026-10-03 の run01〜03 を台本にする。それ以外は台本を作らない。

2026-09-29 のチャンネル調査は正本ではない。YouTube のみ、成功・直接は 18、TikTok は 0、Instagram は未測定。

## コマンド

共通点が `不明` のあいだは inbox に入らない。

```bash
python -m minimaxh3.affi plan --product kanetora --commonalities research/affi/commonalities.yaml
python -m minimaxh3.affi run --one --product kanetora --platform youtube --commonalities research/affi/commonalities.yaml --drive "$H3_DRIVE_ROOT" --ref-dir assets/character
python -m minimaxh3.affi run --count 3 --product all --platform youtube --commonalities research/affi/commonalities.yaml --drive "$H3_DRIVE_ROOT" --ref-dir assets/character
python -m minimaxh3.affi package --drive "$H3_DRIVE_ROOT" --waiting affi-waiting
python -m minimaxh3.affi cutlist render --csv affi-waiting/<id>/cuts.csv --out affi-waiting/<id>/final.mp4 --purpose h3
```

`--one` は使える台本の次の1パートだけを inbox に置く。`--count N` は N 本を待ち行列に積み、inbox に出すのはそのうち1件。サクラは `assets/character/sakura-ref.jpg`（無いときは同じ顔の `docs/affi-stock/first_frames/_ref/sakura_916.jpg`）。犬は `docs/affi-stock/dog-ref.jpg`。Imagine は切る。新しい顔は作らない。

参照が必要なパートは `run_i2v.py`、顔も犬も出さないパートは `run_t2v.py`。R2V は自分で生成した動きの動画が無いので使わない。inbox の画角は 768×1344（9:16）。10/3 の台本の 9 秒パートは 640×1152 だが、grokbot の i2v はそのサイズを受けないので、プロンプトの縦 9:16 はそのまま、ジョブのキャンバスだけ 768×1344 にする。

## H3の代わり（画像スライド）

H3動画が直近で完了条件を満たせないときだけ使う。初稿は1本。

```bash
python -m minimaxh3.affi slide --id orbis-dot-01
bash minimaxh3/affi/slides/orbis-dot-01/build_slide.sh
```

`slide` は初稿のパスと採点を出す。画像は作らない。8枚（表紙、問題提起、5つ、締め）。各3秒。`build_slide.sh` は cut-list-ffmpeg を呼ぶだけ。

```bash
python -m minimaxh3.affi cutlist render \
  --csv minimaxh3/affi/slides/orbis-dot-01/cuts.csv \
  --out minimaxh3/affi/slides/orbis-dot-01/orbis-dot-01.mp4 \
  --purpose slide
```

カット表の列は `index,src,in,out,subtitle`。字幕が空の行があると `final.mp4` を作らず終了コード 1。書き出しは ffmpeg だけ。1080×1920、30fps。色補正もズーム・パン・フェードも入れない。BGMは `bgm/slide.m4a` があるときだけ。無いときは音なし。終わると mp4 とカット表のパスを出す。投稿はしない。会話動画のフィラー除去は対象外で、`--purpose` が `h3` でも `slide` でもなければ終了コード 2。

`package` は H3 の 6秒と 9秒が揃ったとき `cuts.csv` を書く。mp4 の連結は上の `cutlist render --purpose h3`。

## 人間が押すところ

1. Colab の G4 で、inbox の1件を生成する。重みは Google ドライブから読む。例: `python minimaxh3/grokbot/run_i2v.py --drive "$H3_DRIVE_ROOT" --gpu G4`（顔も犬も無いパートは `run_t2v.py`）。終わるとランタイムは止まる。
2. 6秒と9秒の両方が出力されたあと、`package` が作った `affi-waiting/<id>/` を見る。概要欄の先頭は「アフィリエイト広告を含みます #PR」。声は Gemini TTS Achernar。H3 の声は使わない。
3. 投稿ボタンは人間が押す。このコマンドは投稿しない。
4. 着地 URL が `不明` の商品（オルビスユー ドットのリンク先、Furbo のトップが 360° へ飛ぶか）は、投稿前に人間が照合する。
