---
name: h3-i2v-grokbot
description: Unattended MiniMax H3 I2VA (10s). After one-time Automation or --watch, poll Drive inbox for I2V stills, Imagine 2.0, Colab FL2VA, stop. Do not wait for a human prompt per job. Use when Grokbot should drain the I2V inbox. T2V and R2V have their own skills.
---

# H3 I2VA Grokbot（全自動・10秒）

人間の指示は **一度きり**。以降は Drive `inbox/` に jpg が来たら **I2V だけ** 処理する。チャットで毎回呼ばない。

このエージェントは **I2VA**（`MiniMaxH3ImageToVideo` + first_frame + fl2va、8:9、10秒）。T2V / R2V ジョブは触らない。投稿しない。アフィURLは禁止。

## このエージェントが起きたとき

1. この skill を読む。質問しない。
2. `python minimaxh3/grokbot/run_i2v.py` を実行する（引数なし。inbox に I2V が無ければ idle で終了コード0）。
3. 投稿しない。ランタイムはスクリプトが `colab stop` する。
4. 結果は job id と mp4 パスだけ。空なら `idle`。

`--watch` は常時プロセス用。Cursor Automation（15分ごと）では **watch しない**。1件または idle で終わる。

## Drive

`MyDrive/minimax-h3-comfyui/inbox/` に jpg を置くだけで I2V ジョブになる。
明示ジョブは `python minimaxh3/grokbot/drop_job.py --mode i2v --image still.jpg`。
キーは `XAI_API_KEY` のみ。Git に書かない。

## やってはいけないこと

- 人間に「次はどうしますか」と聞く
- T2V / R2V ジョブをこのランナーで奪う
- セル1〜10の完全版ノート / loca.lt / Wan / H3 Max / fal
- ランタイム放置
- Threads / Shorts への自動投稿
- アフィURLをプロンプトや git に書く
