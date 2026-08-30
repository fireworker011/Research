---
name: h3-i2v-grokbot
description: Unattended MiniMax H3 I2VA. Phone Colab + fal is the no-PC path. After one-time Automation or --watch, poll Drive inbox, Imagine 2.0, fal H3 Max. Do not wait for a human prompt per job.
---

# H3 I2VA Grokbot（全自動）

PC が無い・壊れているときは **スマホ Colab** を使う。`run_i2v.py` を要求しない。

https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_i2v_phone.ipynb

鍵に `FAL_KEY`。CPU で全セル実行。inbox / input の jpg が 10 秒動画になる。

Cursor が使えるときは人間の指示は **一度きり**。以降は Drive `inbox/` に jpg が来たら処理する。`--backend colab` のときだけランタイムはスクリプトが `colab stop` する。

完全再現の Comfy I2VA は A100 が要る。PC 無しの最善手は fal-max。R2V / Hailuo / 10Eros / 投稿はしない。アフィURLは禁止。

## このエージェントが起きたとき

1. この skill を読む。質問しない。
2. PC 無しならスマホ Colab の手順を案内して終わる（コード変更が目的でなければ）。Cursor があるなら `python minimaxh3/grokbot/run_i2v.py`（inbox 空なら idle）。
3. 投稿しない。
4. 結果は job id と mp4 パスだけ。空なら `idle`。

## Drive

`MyDrive/minimax-h3-comfyui/inbox/` または `input/` に jpg。キーは Colab シークレットまたは env の `FAL_KEY` / `XAI_API_KEY`。Git に書かない。

## やってはいけないこと

- 人間に「次はどうしますか」と聞く
- セル1〜10の完全版ノートを PC 無しの人に押させる
- loca.lt / R2V / Wan / Hailuo API / 10Eros
- 無料 fal HTML ページのスクレイプ（5秒枠は手試し専用）
- Threads / Shorts への自動投稿
