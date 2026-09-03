---
name: h3-t2v-grokbot
description: Unattended MiniMax H3 T2V (10s, 9:16). After one-time Automation or --watch, poll Drive inbox for prompt txt, Colab FL2VA without first_frame, stop. Use when Grokbot should drain the T2V inbox.
---

# H3 T2V Grokbot（全自動・10秒）

人間の指示は **一度きり**。以降は Drive `inbox/` に `.txt` が来たら **T2V だけ** 処理する。チャットで毎回呼ばない。

公式 T2V は `MiniMaxH3ImageToVideo` に **first_frame を繋がない**。キャンバス 9:16（576×1024）。Grokbot は **10秒**。Imagine しない。静止画は使わない。

## このエージェントが起きたとき

1. この skill を読む。質問しない。
2. `python minimaxh3/grokbot/run_t2v.py` を実行する（引数なし。T2V が無ければ idle で終了コード0）。
3. 投稿しない。ランタイムはスクリプトが `colab stop` する。
4. 結果は job id と mp4 パスだけ。空なら `idle`。

専用 Colab: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_t2v_bot.ipynb

`--watch` は常時プロセス用。Cursor Automation では **watch しない**。1件または idle で終わる。

## Drive

`inbox/` に `prompt.txt` を置くだけで T2V ジョブになる。
明示ジョブは `python minimaxh3/grokbot/drop_job.py --mode t2v --prompt-file prompt.txt`。
キー不要（Imagine しない）。`XAI_API_KEY` は I2V/R2V 用。

## やってはいけないこと

- first_frame を繋ぐ（それは I2V）
- I2V / R2V ジョブをこのランナーで奪う
- loca.lt / Wan / H3 Max / fal
- ランタイム放置
- Threads / Shorts への自動投稿
- アフィURL・収入主張をプロンプトに書く
