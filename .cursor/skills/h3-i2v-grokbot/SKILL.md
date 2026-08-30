---
name: h3-i2v-grokbot
description: Unattended MiniMax H3 I2VA. After one-time Automation or --watch, poll Drive inbox, Imagine 2.0, fal H3 Max (default) or Colab, stop. Do not wait for a human prompt per job. Use when Grokbot or a scheduled agent should drain the I2V inbox.
---

# H3 I2VA Grokbot（全自動）

人間の指示は **一度きり**。以降は Drive `inbox/` に jpg が来たら処理する。チャットで毎回呼ばない。

完全再現は **I2VA**（1枚目が first frame）。R2V / Hailuo API / MiniMax-H3-10Eros-Max / 投稿はしない。アフィURLは禁止。
デフォルト backend は **fal-max**（`minimax/h3-max/image-to-video`）。無料プレイグラウンド（ログインなし・5秒）はスクレイプしない。

## このエージェントが起きたとき

1. この skill を読む。質問しない。
2. `python minimaxh3/grokbot/run_i2v.py` を実行する（引数なし。inbox 空なら idle で終了コード0）。
3. 投稿しない。`--backend colab` のときだけランタイムはスクリプトが `colab stop` する。
4. 結果は job id と mp4 パスだけ。空なら `idle`。

`--watch` は常時プロセス用。Cursor Automation（15分ごと）では **watch しない**。1件または idle で終わる。

## Drive

`MyDrive/minimax-h3-comfyui/inbox/` に jpg を置くだけでジョブになる。
`drop_job.py` は任意。キーは `FAL_KEY` と `XAI_API_KEY`。Git に書かない。

## やってはいけないこと

- 人間に「次はどうしますか」と聞く
- セル1〜10の完全版ノート
- loca.lt / R2V / Wan / Hailuo API / 10Eros
- 無料 fal HTML ページのスクレイプ（5秒枠は手試し専用）
- ランタイム放置（`--backend colab` のとき）
- Threads / Shorts への自動投稿
