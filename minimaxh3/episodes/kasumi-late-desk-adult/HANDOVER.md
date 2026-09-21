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

撮るのは Colab 4 番で分かれる。オフ=同僚□じゅぼ口内口移し → 警備□後背位中出し → 課長□挿入開始＋仰向け正常位。オン=同僚□ベロチュー回避 → 警備△横スク打倒＋じゅぼ → 課長△敗北＋正常位。
Combat はオンの 06 と 10 だけ（prfight2、euler+beta 12）。03/07/11 には積むな。
セックスは体位名ではなく誰がどの方向へ（病棟と同じ）。仰向けは竿役が前へ、受け入れ側の骨盤は床に残す。「hips moving」は動く側の名前。
同枝に `hospital-exit-adult`（病棟脱出。話のドロップダウンで選ぶ。Colab 5 番が全体の既定。シーンごとで誘う・受け入れる・回避）。
UNet は erotic + eros-max だけ。霞東本体・番台・inbox I2V は stock。③に足すな。
inbox / drop_job / run_i2v / Imagine / 投稿 / HQ dump は触るな。霞東 5カット raw は reuse するな。参考バトル mp4 はモーションにしない。
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
| HEAD | 24cm。オフ 03 じゅぼ10秒フル＋口内＋口移し。ななは座位のままフェード。オフ 07 中出し→イキ顔→抜く→垂れ→去り際ベロチュー→青木完全フェード。10 は挿入開始。11 は仰向けのまま同じ位置。マンコの中は竿だけ |
| パック | `minimaxh3/episodes/kasumi-late-desk-adult/` |
| ノート | `minimax_h3_episode_bot.ipynb` |

`colab/h3_episode.py` と `minimaxh3/h3_episode.py` は同期する。③ / `h3_lora_studio.py` は触らない。

## 何を撮るか

オフ約 55 秒・オン約 48 秒。遅刻した朝。参考バトルは約12秒の真横フルボディ → **半分の 5秒**、引き、足まで、水平トラック。オフのななじゅぼは 10 秒フル。青木中出しは 7.5 秒。

| 人 | 歳 | |
|---|---|---|
| みお | 21 | スリム Cカップ。竿なし。トートなし |
| なな | 23 | スリム Dカップ。ふたなり 24cm。机でシコシコ |
| 青木 | 27 | スリム Eカップ。ふたなり 24cm。オフは後背位。オンは倒してじゅぼ |
| 黒木 | 29 | スリム Eカップ。ふたなり 24cm。オフはベロチュー押し倒し＋挿入開始。オンは敗北ピン |

本線は Colab 4 番で分かれる。オフ=じゅぼ口内口移し・後背位中出し・挿入開始から仰向け正常位（戦いなし）。オン=横スク戦い＋じゅぼ＋正常位ピン。混ぜない。

同枝に別スラッグ `hospital-exit-adult`（ボロボロ病棟脱出。話で選ぶ。Colab 5 番が全体の既定。シーンごとで誘う・受け入れる・回避。みき 22cm ふたなり・れい 24cm・かな 20cm 3番目・しの 30cm 4番目・妖艶＋長い舌。登場スキップ・誘うポーズ・道中トイレあり）。

## UNet

- このスラッグ: `lane: erotic` + `checkpoint: eros-max`
- ファイル: Drive `minimax-h3-comfyui/models/diffusion_models/10Eros_Max_h3_TURBO-hybrid_beta5_int8.safetensors`（約21GB）。無ければ HuggingFace `TenStrip/10Eros-Max`
- その上に `balance`（LoRA なし euler 8。turbo 焼き込み済み。シネマ LoRA は積まない）。`speed` / `quality` に切替可。Combat LoRA は Colab 4 番のハイメモリ任意（既定オフ）
- GPU ビートは T2V。`render.camera_pack` 既定 `side2d`（横スク）。`action3d` は Colab `CAMERA` か `--camera`
- 霞東本体・番台に eros-max を書くと check が落とす
- `*-adult` の省略は stock に落ちない（check が落とす）
- 10Eros Max は Drive `models/diffusion_models/10Eros_Max_h3_TURBO-hybrid_beta5_int8.safetensors` を使う。HuggingFace からは取らない。途中切れの別ファイル `.part` は無視。stock には落とさない
- inbox の `*fl2va*` は 10Eros を飛ばす
- LightX2V turbo LoRA はこの UNet に積まない（turbo は焼き込み済み）。Larry も積まない。Combat はハイメモリでオンにしたときだけ。じゅぼは物語集 blowjob LoRA（`bl0w_j0b`、0.8）。DT-sQKV は使わない
- Drive は symlink できない。`diffusion_models` のファイルをそのまま読む
- Comfy は成人レーンで VRAM フラグを付けない（現行 CLI に `--normalvram` は無い。付けると start failed）。stock は `--highvram`

## 次の一手

本番 GPU のつなぎは Colab で選ぶ。迷ったら **カット（本ごと独立）**。カットも **前の最終フレームから続ける** も 1本目は T2V。チェーンは 2本目以降 I2V。**用意した最終フレームへ着く**（stills jpg を最後のコマ）も可。格闘 LoRA は 4 番、既定オフ、オンはハイメモリ専用。声は日本語カナだけ（`voices` の喘ぎ。英語禁止）。カメラは side2d / action3d。プリセットは speed / balance / quality。Colab は slug を切り替えて Run all。Drive は各 `episodes/<slug>/` と `models/erotic/` だけ。スチールは上書きしない。参考 mp4 はモーションにしない。

```bash
cd minimaxh3
python h3_episode.py check  episodes/kasumi-late-desk-adult
python h3_episode.py check  episodes/hospital-exit-adult
python minimaxh3/grokbot/run_episode.py --episode kasumi-late-desk-adult --branch cursor/h3-kasumi-adult-0402
```

## やらないこと

- 霞東本体の上書き。PR #141 マージ。5カット raw の reuse
- 参考バトル mp4 をモーションにする
- ③ / STORY / Qwen / inbox / Imagine / 投稿
- Larry + LightX2V。15秒。キャンバス縮小
- 山田・定時退社・教室・制服・セーラー
- HQ dump / hq-instruct / Threads cron
