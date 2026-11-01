# Wan2.1 VACE 14B Colab 起動手順

生成本体は Wan2.1 VACE 14B。有料 API は使わない。Drive に完全な重みがあればそれを使う。無いファイルは Drive に書かず、Colab の `/content/ComfyUI_models` に取得する。ユーザーのファイルは消さない。

## 起動

1. 次のリンクを開く。  
   https://colab.research.google.com/github/fireworker011/Research/blob/cursor/wan21-vace-14b-colab-702e/colab/h3-wan21-vace/wan21_vace_14b_colab.ipynb
2. ランタイム → ランタイムのタイプを変更 → GPU → **A100** を選んで接続する。T4 や L4 のまま実行すると、最初のコードセルで止まる。
3. 上から順にセルを実行する。途中で Drive の許可が出る。
4. Drive に重みが無いときは、そのファイルだけ Colab のディスクに取得する。Drive の空きは、モデルを Drive に保存するときだけ見る。出力の mp4 は小さい。

## 入力

マイドライブの `ComfyUI_vace_h3/input/` に置くファイル:

- `face_ref.png`
- `controls/C1_control_1b6a.json`
- `controls/C2_control_f32a.json`
- `controls/C3_control_88b5.json`
- `controls/C4_control_6d2a.json`
- `controls/prompts.json`

`face_ref.jpg`、`face_ref.jpeg`、`face_ref.webp` は `face_ref.png` の代わりに1枚だけ使える。顔だけの切り抜き。ノートは縦フレームの上の方へ、比率を保って置き、周囲は灰色にする。この画像を WanVaceToVideo の reference に渡すのは C2 と C4 だけ。

4つの制御 JSON は、このフォルダの同じファイルを中身を変えずに置く。秒数、OpenPose、Depth、カメラはその値のまま使う。`prompts.json` は全カットの固定語ブロック A、C2 と C4 だけのブロック S、カットごとの画の文、共通ネガティブ、C2 の口と C4 の手の追加ネガティブ。

## 出力

マイドライブの `ComfyUI_vace_h3/output/<実行時刻>/`。

- カットごとに `C1.mp4` のような 9:16（720×1280）の mp4 が1本
- 使った制御 JSON のコピー

残すフレーム数は、制御 JSON の `duration_s × fps` を丸めた枚数（C2 は 84 枚、24fps）。VACE の長さはそれ以上で最小の 4n+1 なので、その枚数だけ生成してから正確な枚数へ切る。ffprobe で枚数と 720×1280 を確認する。

OpenPose、マスク、顔参照は WanVaceToVideo の `control_video` / `control_masks` / `reference_image` にだけ渡す。保存する mp4 はサンプラーと VAE の出力だけ。先頭フレームが制御フレームに近い（SSIM > 0.6）、または骨格の原色が残っているときは、その実行を失敗にする。深度の楕円は制御 RGB に合成しない。

書き出したあと、ffmpeg で 1〜2px の手ブレと、1回のフォーカス送りを焼く。

A100 40GB では 480×832 で生成し、書き出し時に 720×1280 へ収めて上下に細い黒帯を付ける。A100 80GB 以上は 720×1280 のまま生成する。4カットを書いたあと、最後のセルが `drive.flush_and_unmount()` を呼んでからランタイムを切断して削除する。生成に失敗したときも、同じように flush して削除する。

テロップは映像に焼かない。JSON の `caption` は映像プロンプトに入れない。発話はあとから声として足す。プロンプトのキーフレーム時刻は、台本全体の時刻ではなく、そのカットの開始からの秒数。

## ライセンス

このノートが取得する重みは、次のオープンライセンスのものだけ。

- Wan2.1-VACE-14B（`wan2.1_vace_14B_fp16.safetensors`）: Apache-2.0。元は [Wan-AI/Wan2.1-VACE-14B](https://huggingface.co/Wan-AI/Wan2.1-VACE-14B)。ComfyUI 用ファイルは [Comfy-Org/Wan_2.1_ComfyUI_repackaged](https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged) の再パック。
- UMT5-XXL（`umt5_xxl_fp8_e4m3fn_scaled.safetensors`）: Apache-2.0。元は Google の UMT5-XXL で、fp8 はその量子化。
- Wan2.1 VAE（`wan_2.1_vae.safetensors`）: Apache-2.0（Wan2.1 に含まれる）。
- ComfyUI: GPL-3.0。起動時に取得する。このリポジトリには同梱しない。

OpenPose と Depth の学習済み重みは入れない。制御画像は JSON のキーフレームからノートが描く。カメラは `camera_vector`（移動はピクセル、回転は度、手ブレは `amp_px`）で、その制御画像を動かして VACE に渡す。手首の 1cm はフレーム高さの 2% として描く。Wan Fun Camera 14B は別の約 32GB モデルで、VACE 14B と同時には A100 40GB に載らないため使わない。

## 検証の範囲

JSON の読み込み、制御画像の作成、ノートの構文、フレーム数の切り出し、無地フレームからの 9:16 mp4 連結、手ブレとフォーカス送り、制御画像そのものを弾く検査はローカルで確認した。A100 でのモデル取得と VACE の生成は、この環境では未実施。

ノートのセルは `logic.py` と `cells/` が元です。直したあとは `python3 build_notebook.py` と `python3 test_notebook.py` を実行する。
