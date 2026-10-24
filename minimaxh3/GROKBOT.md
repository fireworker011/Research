# 一度だけ。以降は inbox にファイルを置くだけ。

Naomi が Grokbot に話しかけるのは初回の Automation 登録（または `--watch` 起動）だけ。
ジョブが来るたびに指示しない。T2V / I2V / R2V は **別エージェント**。混ぜない。

Grokbot の動画はどれも **10秒**。投稿は人間。リンクはプロフィール。アフィURLは git / プロンプト禁止。

## 初回（人間が1回）

1. Colab Pro + `pip install google-colab-cli` + 一度 `colab new` でログイン
2. I2V / R2V の still を整えるならシェルに `XAI_API_KEY`（Git禁止）
3. Cursor → Automations を **3つ**。スケジュール **15分ごと**。プロンプトは下をそのまま。

### I2V（8:9・first_frame・FL2VA）

```
skill h3-i2v-grokbot を読む。
inbox の I2V を1件だけ処理して終了する（空なら idle で終わる。待たない。質問しない）。
python minimaxh3/grokbot/run_i2v.py
投稿するな。T2V/R2V/Wan/Max/完全版ノート/loca.lt は使うな。終わったら colab stop。
空のときは「idle」とだけ書いて終わる。
```

### T2V（9:16・first_frame なし・FL2VA）

```
skill h3-t2v-grokbot を読む。
inbox の T2V を1件だけ処理して終了する（空なら idle で終わる。待たない。質問しない）。
python minimaxh3/grokbot/run_t2v.py
投稿するな。I2V/R2V/Wan/Max/完全版ノート/loca.lt は使うな。終わったら colab stop。
空のときは「idle」とだけ書いて終わる。
```

### R2V（still=identity・mp4=motion・ref2va）

```
skill h3-r2v-grokbot を読む。
inbox の R2V を1件だけ処理して終了する（空なら idle で終わる。待たない。質問しない）。
python minimaxh3/grokbot/run_r2v.py
投稿するな。参照動画を外すな。ponz原作をmotionにするな。Wan/Max/完全版ノート/loca.lt は使うな。終わったら colab stop。
空のときは「idle」とだけ書いて終わる。
```

常時PCがあるなら Automation の代わりにこれでもよい（これも一度だけ）:

```bash
python minimaxh3/grokbot/run_i2v.py --watch
python minimaxh3/grokbot/run_t2v.py --watch
python minimaxh3/grokbot/run_r2v.py --watch
```

セッション名は `h3-i2v` / `h3-t2v` / `h3-r2v`。GPU は A100（`--high-mem`）。R2V の確実な10秒は 80GB。

## bot 専用 Colab（モードごと 1ノート）

コードセルは1本。inbox が空なら idle でランタイムを手放す。人間用のスマホノートとは別。

| bot | 専用 Colab（GitHub） | Drive 上の同じノート |
|---|---|---|
| T2V | [minimax_h3_t2v_bot.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_t2v_bot.ipynb) | [Drive](https://colab.research.google.com/drive/1ST6gGKP7T3leIDoozk7jfV30dEXA6m8-) |
| I2V | [minimax_h3_i2v_bot.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_i2v_bot.ipynb) | [Drive](https://colab.research.google.com/drive/1myFp5BxF7JlaQvgm5PeMj-FFIOKT4yUE) |
| R2V | [minimax_h3_r2v_bot.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_r2v_bot.ipynb) | [Drive](https://colab.research.google.com/drive/1uon_V60eQo7rfiyG5P4JXhX6JksBpsbZ) |
| エピソード | [minimax_h3_episode_bot.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-episode-oneclick-f112/minimax_h3_episode_bot.ipynb) | （inbox と別。`episodes/<slug>/`） |

Grokbot の `run_*.py` は同じ処理を `google-colab-cli` で `h3_*_colab_main.py` として exec する。ノートを開いて Run all しても同じ 1件処理。

## 以降（全自動）

Drive `minimax-h3-comfyui/inbox/`

| 置き方 | モード |
|---|---|
| jpg だけ | I2V |
| `.txt` だけ | T2V |
| フォルダに still + mp4 | R2V |
| `drop_job.py --mode …` | 明示 |

完成: `minimax-h3-comfyui/output/{id}.mp4`

## 16:9（横動画）

デフォルトは T2V=9:16、I2V オマージュ=8:9。横は **1024×576**（H3 は 32 倍数。1280×720 は不可）。

スマホ T2V: [minimax_h3_t2v_phone.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_t2v_phone.ipynb) の ③で `ASPECT` を `16:9`。

```bash
python minimaxh3/grokbot/drop_job.py --mode t2v --aspect 16:9 --prompt-file prompt.txt
```

I2V を 16:9 にするなら横の still が要る（オマージュ 8:9 はそのまま）。`--aspect 16:9`。Hailuo API ノートの RATIO は使わない。

## エピソード一発（別系統・inbox を使わない）

複数ビートの完成動画（HUD・カード・連結つき）は **`episodes/<slug>/`** の別ルート。inbox に置かない（裸 jpg はココナラ I2V になる）。
**15分 Automation には登録しない。** 1回の実行 = 1本の完成 mp4。手順は `minimaxh3/episodes/README.md`。skill は `h3-episode-oneclick`（作る）と `h3-episode-grokbot`（回す）。

Grokbot に話しかけるのはこのブロックをそのまま。slug だけ変える。

### 番台ディストリクト 短縮版（25秒・ミッション失敗で落ちる。次はこれ）

`bandai-district/raw/` の暖簾・自転車・軽トラをそのまま使い、GPU で描くのは理容室 1 本だけ（約 7 分）。

```
skill h3-episode-grokbot を読む。
質問しない。inbox は触るな。I2V/T2V/R2V ランナーは動かすな。Imagine するな。
python minimaxh3/grokbot/run_episode.py --episode bandai-district-short
投稿するな。Wan/Max/完全版ノート/loca.lt/LoRAスタジオは使うな。終わったら colab stop。
結果は slug と Drive episodes/bandai-district-short/final/latest.mp4 のパスだけ。失敗なら status.json のエラー一行。
```

### 番台ディストリクト 92秒版（続きから。raw があるビートは飛ばす）

```
skill h3-episode-grokbot を読む。
質問しない。inbox は触るな。I2V/T2V/R2V ランナーは動かすな。Imagine するな。
python minimaxh3/grokbot/run_episode.py --episode bandai-district
投稿するな。Wan/Max/完全版ノート/loca.lt/LoRAスタジオは使うな。終わったら colab stop。
結果は slug と Drive episodes/bandai-district/final/latest.mp4 のパスだけ。失敗なら status.json のエラー一行。
```

### 全部作り直し（`--fresh`）

```
skill h3-episode-grokbot を読む。
質問しない。inbox は触るな。I2V/T2V/R2V ランナーは動かすな。Imagine するな。
python minimaxh3/grokbot/run_episode.py --episode bandai-district --fresh
投稿するな。Wan/Max/完全版ノート/loca.lt/LoRAスタジオは使うな。終わったら colab stop。
結果は slug と Drive episodes/bandai-district/final/latest.mp4 のパスだけ。失敗なら status.json のエラー一行。
```

### 別ネタ（slug を差し替え）

```
skill h3-episode-grokbot を読む。
質問しない。inbox は触るな。I2V/T2V/R2V ランナーは動かすな。Imagine するな。
python minimaxh3/grokbot/run_episode.py --episode <slug>
投稿するな。Wan/Max/完全版ノート/loca.lt/LoRAスタジオは使うな。終わったら colab stop。
結果は slug と Drive episodes/<slug>/final/latest.mp4 のパスだけ。失敗なら status.json のエラー一行。
```

`<slug>` は `minimaxh3/episodes/<slug>/episode.json` があること。無ければ GitHub の同パスから取る。テンプレから新ネタを足す作業は skill `h3-episode-oneclick`（コードは触らない）。

スマホは `minimax_h3_episode_bot.ipynb` を Run all。セッション名 `h3-episode`。GPU は A100（`--high-mem`）。

投稿は人間。リンクはプロフィール。
