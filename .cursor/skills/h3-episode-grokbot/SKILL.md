---
name: h3-episode-grokbot
description: One-shot MiniMax H3 episode render. After one explicit prompt, run run_episode.py for a slug, Colab renders every beat, HUD+cards+stitch, stop. Not a 15-minute Automation. Not the Coconala I2V/T2V/R2V inbox bots. Use when Grokbot should finish one episode mp4.
---

# H3 エピソード Grokbot（一発・完成動画）

人間の指示は **一度きり**。`run_episode.py --episode <slug>` を実行し、Drive `episodes/<slug>/final/latest.mp4` が出たら終わる。チャットで毎回呼ばない。15分スケジュールに登録しない。inbox は触らない。

このエージェントは **エピソード一発**（`episode.json` → 全ビート I2V/chain/T2V → HUD → タイトル／免責エンドカード → xfade 連結）。I2V / T2V / R2V ジョブは触らない。投稿しない。アフィURLは禁止。Imagine しない。

## このエージェントが起きたとき

1. この skill と `minimaxh3/episodes/README.md` を読む。質問しない。
2. チャットに slug が無ければ `bandai-district-short`（25秒・失敗落ち。`bandai-district/raw/` を reuse し理容室 1 本だけ描く）。`--fresh` と書いてあれば `--fresh`（reuse 元は消さない。描き直すのは自分の raw だけ）。
3. `python minimaxh3/grokbot/run_episode.py --episode <slug>` を実行する（必要なら `--preset daily` / `--fresh`）。
4. 投稿しない。ランタイムはスクリプトが `colab stop` する。
5. 結果は slug と `episodes/<slug>/final/latest.mp4` のパスだけ。失敗なら `status.json` のエラー一行。

専用 Colab: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-episode-oneclick-f112/minimax_h3_episode_bot.ipynb

`--watch` は無い。Cursor Automation（15分ごと）には登録しない。1エピソードで終わる。

## Drive

`MyDrive/minimax-h3-comfyui/episodes/<slug>/` だけ使う（`episode.json` と `stills/`。無ければ GitHub から取る）。
本番 `inbox/` `queued/` `output/` にファイルを置かない。helper キャッシュは `episodes/_lib/` だけ。
キー不要（Imagine しない）。`XAI_API_KEY` は要求するな。

途中で止まっていたら `raw/<beat>.mp4` があるビートは飛ばす。全部作り直しは `--fresh`。

## やってはいけないこと

- 人間に「次はどうしますか」と聞く
- I2V / T2V / R2V ジョブをこのランナーで奪う。`drop_job.py` / `run_i2v.py` を動かす
- 本番 inbox に jpg を置く
- 15分 Automation を足す。`--watch` する
- セル1〜10の完全版ノート / loca.lt / Wan / H3 Max / fal / LoRA スタジオ③
- ランタイム放置
- Threads / Shorts への自動投稿
- アフィURLをプロンプトや git に書く
- 参照元の動画・音声をモーションにする
