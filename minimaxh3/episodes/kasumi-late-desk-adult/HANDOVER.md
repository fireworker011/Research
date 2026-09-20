# 霞東アダルト予告 引き継ぎ（コンバット・Eros Max）

既存エロ動画（③ / STORY / Qwen 編集）とは**別チャット**。混ぜるな。
このパックだけを続ける。質問せず、下を読んでから作業する。

## 新規チャットに貼る文

```
霞東アダルト予告（コンバット入り）を続ける。既存エロ動画（③ / STORY / Qwen）は別チャット。触るな。Naomiichi。

まず読め:
- `minimaxh3/episodes/kasumi-late-desk-adult/HANDOVER.md`
- `.cursor/skills/h3-episode-oneclick/SKILL.md`
- `minimaxh3/episodes/kasumi-late-desk-adult/PREP.md`
- `minimaxh3/episodes/kasumi-late-desk-adult/SCRIPT.md`
- `minimaxh3/episodes/README.md` の UNet レーンと霞東あさ

作業ブランチ: `cursor/h3-kasumi-adult-0402` だけ。新枝禁止。
ベース: `cursor/h3-ol-late-desk-33d9`
PR: #142 draft。#141（霞東本体）は上書きするな。マージするな。
slug: `kasumi-late-desk-adult`
Colab: `minimax_h3_episode_bot.ipynb` の EPISODE=kasumi-late-desk-adult / BRANCH=cursor/h3-kasumi-adult-0402

撮るのは □口説く×3。Combat は 06 だけ（trigger 空、euler+beta 12）。03 と 10 には積むな。
UNet は erotic + eros-max だけ。霞東本体・番台・inbox I2V は stock。③に足すな。
inbox / drop_job / run_i2v / Imagine / 投稿 / HQ dump は触るな。霞東 5カット raw は reuse するな。
```

## チャットの分け方

| チャット | 中身 | 枝 |
|---|---|---|
| **ここ（新規）** | 霞東アダルト予告。コンバット 06。Eros Max | `cursor/h3-kasumi-adult-0402` |
| 既存エロ動画 | ③ / STORY / アナル三択 | `cursor/h3-anal-stories-f112` / PR #138 |
| 画像編集 | Qwen Edit NSFW | 同じ anal 枝。`qwen-image-edit-nsfw/HANDOVER.md` |
| 霞東本体（非エロ） | ぶっとび三戦 | `cursor/h3-ol-late-desk-33d9` / PR #141 |

既存エロ側の入口: https://cursor.com/agents/bc-01a0b6ff-8026-7459-832c-0ad37dfc0402  
画像編集: https://cursor.com/agents/bc-01a0b7ab-9f91-779d-84da-7fd219328566

## いまの枝

| 項目 | 値 |
|---|---|
| 作業 | `cursor/h3-kasumi-adult-0402` |
| ベース | `cursor/h3-ol-late-desk-33d9` |
| PR | https://github.com/fireworker011/Research/pull/142 draft |
| HEAD | ノート既定を adult / `cursor/h3-kasumi-adult-0402` に固定。Combat は 06 だけをテストでロック |
| パック | `minimaxh3/episodes/kasumi-late-desk-adult/` |
| ノート | `minimax_h3_episode_bot.ipynb` |

`colab/h3_episode.py` と `minimaxh3/h3_episode.py` は同期する。③ / `h3_lora_studio.py` は触らない。

## 何を撮るか

約 45 秒（12ビート ≈ 44.9s）。遅刻した朝、全裸の成人が四択の□口説くを三回選んで自席へつく。失敗は「隣の席に座った」。

| 人 | 歳 | |
|---|---|---|
| みお | 27 | 竿なし |
| 青木 | 44 | ふたなり 20cm |
| 黒木 | 48 | ふたなり 20cm |
| なな | 29 | 竿なし |

本線: カバー → コマンド警備 → ジュボ（03 chain）→ 覗き → コマンド課長 → **押し倒し＋挿入（06 Combat）** → 「コピー です」→ 席列 → コマンド同僚 → 密着 → かばん → 着席 → 失敗。

Combat は 06 だけ。trigger 空。本体霞東の 03/06/10 三戦とは別。△戦いは SCRIPT に残して撮らない。

## UNet

- このスラッグ: `lane: erotic` + `checkpoint: eros-max`
- ファイル: `models/erotic/10Eros_Max_H3_FL2VA-INT8-ConvRot.safetensors`（約 22.5GB。初回だけ fetch）
- その上に daily（Larry + cinema）。06 だけ Combat V2
- 霞東本体・番台に eros-max を書くと check が落とす
- `*-adult` の省略は stock に落ちない（check が落とす）
- inbox の `*fl2va*` は 10Eros を飛ばす
- TURBO-hybrid / DT-sQKV は使わない

## 次の一手

本番 I2V はまだ。Drive に `kasumi-late-desk-adult/` は無い。Eros Max FL2VA も Drive に無い（あるのは TURBO-hybrid。使わない）。Colab で Run all。Drive は `episodes/kasumi-late-desk-adult/` と `models/erotic/` だけ。スチールは上書きしない。霞東本体の raw は触るな。

このブランチの `minimax_h3_episode_bot.ipynb` 既定は adult。`run_episode.py` の DEFAULT_BRANCH もこの枝。Run all のまま霞東本体へ行かない。

```bash
cd minimaxh3
python h3_episode.py check  episodes/kasumi-late-desk-adult
python minimaxh3/grokbot/run_episode.py --episode kasumi-late-desk-adult --branch cursor/h3-kasumi-adult-0402
```

任意: 同じスチール・同じ seed で 03 と 06 だけ stock vs Eros を並べる。GPU A/B は未実施。

## やらないこと

- 霞東本体の上書き。PR #141 マージ。5カット raw の reuse
- ③ / STORY / Qwen / inbox / Imagine / 投稿
- Larry + LightX2V。15秒。キャンバス縮小
- 山田・定時退社・教室・制服・セーラー
- HQ dump / hq-instruct / Threads cron
