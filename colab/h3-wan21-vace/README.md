# Wan2.1 VACE 14B Colab 起動手順

既存の `wan22_i2v_lightx2v_colab.ipynb` と同じく、モデルは Google Drive に一度置いて再利用する。生成本体は Wan2.1 VACE 14B。有料 API は使わない。

## 起動

1. 次のリンクを開く。  
   https://colab.research.google.com/github/fireworker011/Research/blob/cursor/wan21-vace-14b-colab-702e/colab/h3-wan21-vace/wan21_vace_14b_colab.ipynb
2. ランタイム → ランタイムのタイプを変更 → GPU → **A100** を選んで接続する。T4 や L4 のまま実行すると、最初のコードセルで止まる。
3. 上から順にセルを実行する。途中で Drive の許可が出る。
4. 初回はモデル約 39GB を Drive に置く。2回目以降は同じファイルを使う。

## 入力

マイドライブの `ComfyUI_vace_h3/input/`。

- `face_ref.png`（jpg / webp も可）。顔だけの切り抜き。ノートは縦フレームの上の方へ、比率を保って置き、周囲は灰色にする。
- `controls/` に、このフォルダの `controls/*.json` を中身を変えずに置く。1カットずつ読む。秒数、OpenPose、Depth、カメラをその JSON の値のまま使う。

## 出力

マイドライブの `ComfyUI_vace_h3/output/<実行時刻>/`。

- カットごとに `C1.mp4` のような 9:16（720×1280）の mp4 が1本
- 使った制御 JSON のコピー

VACE のフレーム数は 4 の倍数+1、最大 81 枚に揃える。JSON の秒数 × fps とずれて、長いカットは少し短くなる。

A100 40GB では 480×832 で生成し、書き出し時に 720×1280 へ収めて上下に細い黒帯を付ける。A100 80GB 以上は 720×1280 のまま生成する。最後のセルは、全部のファイルが書けたあとランタイムを切断して削除する。失敗したときは消さない。

テロップは映像に焼かない。JSON の `caption` は、画面文字にしない発話としてプロンプトへ渡す。

## ライセンス

このノートが取得する重みは、次のオープンライセンスのものだけ。

- Wan2.1-VACE-14B（`wan2.1_vace_14B_fp16.safetensors`）: Apache-2.0。元は [Wan-AI/Wan2.1-VACE-14B](https://huggingface.co/Wan-AI/Wan2.1-VACE-14B)。ComfyUI 用ファイルは [Comfy-Org/Wan_2.1_ComfyUI_repackaged](https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged) の再パック。
- UMT5-XXL（`umt5_xxl_fp8_e4m3fn_scaled.safetensors`）: Apache-2.0。元は Google の UMT5-XXL で、fp8 はその量子化。
- Wan2.1 VAE（`wan_2.1_vae.safetensors`）: Apache-2.0（Wan2.1 に含まれる）。
- ComfyUI: GPL-3.0。起動時に取得する。このリポジトリには同梱しない。

OpenPose と Depth の学習済み重みは入れない。制御画像は JSON のキーフレームからノートが描く。カメラは `camera_vector`（移動はピクセル、回転は度、手ブレは `amp_px`）で、その制御画像を動かして VACE に渡す。手首の 1cm はフレーム高さの 2% として描く。Wan Fun Camera 14B は別の約 32GB モデルで、VACE 14B と同時には A100 40GB に載らないため使わない。

## 検証の範囲

JSON の読み込み、制御画像の作成、ノートの構文、無地フレームからの 9:16 mp4 連結はローカルで確認した。A100 でのモデル取得と VACE の生成は、この環境では未実施。

ノートのセルは `logic.py` と `cells/` が元です。直したあとは `python3 build_notebook.py` と `python3 test_notebook.py` を実行する。
