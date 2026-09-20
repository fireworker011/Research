# 霞東フロア あさ — 再現度のための準備

霞東リライト（`kasumi-late-desk` / PR #141）の文法を成人エロ予告に写した。本体は上書きしない。
Drive の 25秒 latest.mp4 は初回5カットなので見るな・reuse するな。

## 借りる文法（エロでも外さない）

- 三人称ゲームカメラ、カバー、覗き、四択コマンド（後載せ HUD）、失敗カード。映像はオリジナル
- 反転: 退勤ではなく遅刻した朝に自席へつく。落ちは完了ではなく失敗
- 生成は 10秒。見せるのは trim 3〜6秒。`clip_seconds` 15 は禁止。OOM はキャンバスを縮めず 10→8→6
- エンジン上限 12ビート。ui は先頭禁止・連続禁止。still → ui → still
- 顔が見えるのは会話 1本だけ（07）。他は横・後ろ・肩
- HUD は生成後 `h3_hud.py`。スチールにミニマップ・黄枠・時計・字幕を焼くな
- プロンプトは英語。台詞だけかな。看板・名札・紙は無地
- 原クリップ・参照 mp4・音声は R2V / モーション / 素材にするな
- 「slow motion」「slow-mo」「slowly」は書くな
- 同じ場所の続きは `still_as: last`。カバーは `both`。覗き・席列は切ってスチール先頭
- 03 は 01 から chain。接触のあと 07 だけ chain で二行
- Drive の episode.json を手で短いまま残すな。GitHub の 12ビートが正

## この予告で撮るルート

□口説く ×3（警備ジュボ → 課長押し倒し → 同僚密着）。△戦いは SCRIPT に残して撮らない。
全員全裸。青木 44・黒木 48 はふたなり。みお 27・なな 29 は竿なし。年齢は lock に数字。
Combat は 06 だけ `extra_loras: ["combat"]`、trigger 空、euler+beta 12step。03 と 10 には積まない。
土台 UNet は `render.lane: erotic` + `render.checkpoint: eros-max`（`models/erotic/10Eros_Max_H3_FL2VA-INT8-ConvRot.safetensors`）。霞東本体・番台は stock。フォルダ先頭の `*fl2va*` 任せにしない。Larry + cinema はその上。TURBO-hybrid / DT-sQKV は使わない。

## やらないこと

- 霞東本体の上書き。5カット raw の reuse
- 原 mp4 / 音声を素材・モーションにする
- 山田・定時退社・働き方改革・「5 分だけ」・17:58・教室・制服・セーラー
- 飛び蹴り・爆発・血。HP を減らす
- Imagine 2.0、投稿、アフィ URL、inbox、LoRA スタジオ③
- Larry と LightX2V の同時積み
