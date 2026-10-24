---
name: h3-r2v-grokbot
description: Unattended MiniMax H3 R2V (10s). Identity from a still, motion from a video. Colab MiniMaxH3ReferenceToVideo + ref2va. After one-time Automation or --watch, drain the R2V inbox and stop. Use when Grokbot should run reference-to-video.
---

# H3 R2V Grokbot（全自動・10秒）

人間の指示は **一度きり**。以降は Drive `inbox/` に **静止画 + モーション mp4** が来たら **R2V だけ** 処理する。チャットで毎回呼ばない。

ノードは `MiniMaxH3ReferenceToVideo` + **ref2va** unet（fl2va LoRA を載せない）。identity は still、motion は video。OOM しても **参照動画は外さない**。Grokbot は **10秒を先に試し**、足りなければ長さだけ落とす。

オマージュ広告の ponz 原クリップを motion に使うな。別キャラの振り付けガイドだけ。

## このエージェントが起きたとき

1. この skill を読む。質問しない。
2. `python minimaxh3/grokbot/run_r2v.py` を実行する（引数なし。R2V が無ければ idle で終了コード0）。
3. 投稿しない。ランタイムはスクリプトが `colab stop` する。
4. 結果は job id と mp4 パスだけ。空なら `idle`。

専用 Colab: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_r2v_bot.ipynb

`--watch` は常時プロセス用。Cursor Automation では **watch しない**。1件または idle で終わる。

## Drive

inbox に still+mp4 のフォルダを置くか、
`python minimaxh3/grokbot/drop_job.py --mode r2v --image still.jpg --video motion.mp4`。
キーは `XAI_API_KEY`（Imagine 2.0 で still を整える。`--no-imagine` 可）。Git に書かない。

A100 40GB は 10秒が OOM することがある。スクリプトが match / 短い秒数へ落とす。確実な 10秒は A100 80GB High Memory。

## やってはいけないこと

- 参照動画を外して I2V にフォールバックする
- fl2va LoRA を ref2va に載せる
- I2V / T2V ジョブをこのランナーで奪う
- ponz 原作クリップを motion にする
- loca.lt / Wan / H3 Max / fal
- ランタイム放置
- Threads / Shorts への自動投稿
- アフィURLをプロンプトや git に書く
