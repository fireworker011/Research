---
name: h3-episode-oneclick
description: One-click MiniMax H3 episode trailers (episode.json → all beats → HUD → cards → stitched mp4). Use when the user wants a finished game-style homage video, a new topic from the template, a stills preview, or to run/resume an episode on Colab. Not the Coconala I2V bot, not the LoRA studio.
---

# h3-episode-oneclick

質問しない。入力は `minimaxh3/episodes/<slug>/episode.json` とクリーンなスチールだけ。説明書は `minimaxh3/episodes/README.md`。

## やること

1. `cd minimaxh3 && python h3_episode.py check episodes/<slug>` が通るまで `episode.json` を直す（英語本文、台詞はかなだけ、`homage.never`、免責）。`check` は各ビートの窓・小道具・予定尺と、`reuse` 元が Drive/ローカルにあるかを出す
2. GPU なしの確認は `python h3_episode.py stills episodes/<slug> --out /tmp/ep/<slug>`（スチール予告）か `dry-run`。`--out` は slug 名で終わらせる（`reuse` は親フォルダの兄弟 `episodes/<元slug>/raw/` を見る）
3. 本番は Colab ノート `minimax_h3_episode_bot.ipynb` の Run all、または Grokbot に `minimaxh3/GROKBOT.md` のエピソード命令をそのまま貼る（`python minimaxh3/grokbot/run_episode.py --episode <slug>`）。1ランタイムで全ビート → HUD → 連結 → 停止。回すだけのエージェントは skill `h3-episode-grokbot`
4. 途中で落ちたら `raw/<beat>.mp4` を残したまま再実行（続きから）。作り直しは `--fresh`
5. 新しいネタは `minimaxh3/episodes/_template` を複製し、slug・キャスト・ビート・スチールを差し替える。コードは触らない
6. `colab/h3_*.py` と `minimaxh3/h3_*.py` を直したら両方に同じ内容をコピーし、`colab/test_h3_episode.py` を通す

## 本家の文法（README の比較表が根拠。ここを外すと初回版の崩れ方に戻る）

- 映像は日常のまま、HUD の文字だけが犯罪ゲーム。`tone: "mundane"` を既定にする。爆発・ジャンプ・格闘・追跡は否定形でも書かない（H3 は名前を出した物を描く）
- 小道具は `beat.props` でそのビートに要る物だけ。全ビートに全小道具を入れない（軽トラが全ショットに出た原因）
- 1 カット 3〜6 秒。生成は 10 秒のまま `trim` で窓を切る。カットは 4〜5 本、`ui` メニュー 1 本、最後は `cards.fail` の黒テロップ。全体 20〜25 秒
- 会話は `hud.visible: false` で字幕だけ。ミッション行は `mission_keyword` で目的語を赤に
- 顔ショットは 2 本まで。使える raw は `reuse` して再生成しない
- 落ちは「ミッション失敗 ＋ 淡々とした理由一行」。完了で終わらせない

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
