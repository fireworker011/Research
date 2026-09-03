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

| bot | 専用 Colab |
|---|---|
| T2V | [minimax_h3_t2v_bot.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_t2v_bot.ipynb) |
| I2V | [minimax_h3_i2v_bot.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_i2v_bot.ipynb) |
| R2V | [minimax_h3_r2v_bot.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_r2v_bot.ipynb) |

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

投稿は人間。リンクはプロフィール。
