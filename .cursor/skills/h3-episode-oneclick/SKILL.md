---
name: h3-episode-oneclick
description: One-click MiniMax H3 episode trailers (episode.json → all beats → HUD → cards → stitched mp4). Use when the user wants a finished game-style homage video, a new topic from the template, a stills preview, or to run/resume an episode on Colab. Not the Coconala I2V bot, not the LoRA studio.
---

# h3-episode-oneclick

質問しない。入力は `minimaxh3/episodes/<slug>/episode.json` とクリーンなスチールだけ。説明書は `minimaxh3/episodes/README.md`。

## やること

1. `cd minimaxh3 && python h3_episode.py check episodes/<slug>` が通るまで `episode.json` を直す（英語本文、台詞はかなだけ、`homage.never`、免責）
2. GPU なしの確認は `python h3_episode.py stills episodes/<slug> --out /tmp/ep`（スチール予告）か `dry-run`
3. 本番は Colab ノート `minimax_h3_episode_bot.ipynb` の Run all、または Grokbot に `minimaxh3/GROKBOT.md` のエピソード命令をそのまま貼る（`python minimaxh3/grokbot/run_episode.py --episode <slug>`）。1ランタイムで全ビート → HUD → 連結 → 停止。回すだけのエージェントは skill `h3-episode-grokbot`
4. 途中で落ちたら `raw/<beat>.mp4` を残したまま再実行（続きから）。作り直しは `--fresh`
5. 新しいネタは `minimaxh3/episodes/_template` を複製し、slug・キャスト・ビート・スチールを差し替える。コードは触らない
6. `colab/h3_*.py` と `minimaxh3/h3_*.py` を直したら両方に同じ内容をコピーし、`colab/test_h3_episode.py` を通す

## やってはいけないこと

- 本番 Drive の `inbox/queued/running/done/failed/input/output` にエピソードのファイルを置く（ココナラ I2V が拾う）
- `drop_job.py` / `run_i2v.py` / 15分 Automations にエピソードを流す。エピソード用の Automation を足す
- HUD を焼いた画像を先頭フレームにする（HUD は生成後に載せる）
- H3 に日本語 UI・字幕・ミニマップ・透かしを描かせる文
- 参照元の物・人名・小道具、実在ゲーム／格ゲーの名前、Pollo / Seedance をプロンプトに書く
- 子供、流血、怪我。台詞に漢字。顔が見えない本に台詞
- Imagine 2.0 を呼ぶ。`XAI_API_KEY` を要求する
- Larry と LightX2V を同時に積む。OOM でキャンバスを縮める（秒数だけ落とす）
- 1280×720 をそのまま H3 に渡す（1024×576 に正規化される。手で変えない）
- 参照元の動画や音声をモーション参照・素材に使う
- Threads / Shorts へ投稿する。アフィ URL・収入主張を書く
- `h3_lora_studio.py`・③・STORY に足す。本番ルート直下の helper 同名ファイルを上書きする
