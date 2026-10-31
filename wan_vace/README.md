# Wan2.1 VACE 14B（Colab）

縦 9:16 の mp4 を、ComfyUI の Wan2.1 VACE 14B で作ります。参照画像、OpenPose、Depth、カメラの揺れを同時に使います。有料の外部 API は使いません。

生成用ノート（A100）:

https://colab.research.google.com/github/fireworker011/Research/blob/cursor/wan21-vace-colab-a736/wan21_vace_colab.ipynb

ダウンロード用ノート（CPU・1回だけ）:

https://colab.research.google.com/github/fireworker011/Research/blob/cursor/wan21-vace-colab-a736/wan21_vace_download_colab.ipynb

## 起動手順

1. 上の **ダウンロード用** リンクを開く。
2. メニューの **ランタイム → ランタイムのタイプを変更** で、ハードウェアアクセラレータを **なし（CPU）** にする。GPU のままだとノートが止まります。GPU の時間を使わないためのノートです。
3. 上からセルを順に実行する。Google Drive の接続を聞かれたら許可する。
4. 終わるまでそのタブを閉じない。fp16 の本体は約 32GB、fp8 は約 16GB で、テキストエンコーダと VAE と LoRA も入ります。同じ大きさのファイルが Drive に既にあるものは飛ばします。
5. 終わったら最後のセルを実行して、CPU のランタイムを消す。
6. 顔だけの画像を、Drive の `マイドライブ/minimax-h3-comfyui/refs/sakura-face-crop.jpg` として置く。C2 と C4（サクラが映るカット）で使います。この画像は自動では落ちません。
7. 上の **生成用** リンクを開く。
8. **ランタイム → ランタイムのタイプを変更 → A100 GPU** を選ぶ。A100 は Colab Pro の一覧に出ます。T4 や L4 ではノートが止まります。
9. 上からセルを順に実行する。Drive の接続を聞かれたら、さきほどと同じアカウントを許可する。
10. 起動セルが印刷する `COMFY_URL=` の URL が、ComfyUI の画面です。開いて待っても、開かずに待っても結果は同じです。ブラウザのタブは閉じない。
11. 生成セルが `WROTE .../C4.mp4` まで出したら、Drive の `マイドライブ/minimax-h3-comfyui/outputs/trial-01/` に `C1.mp4` `C2.mp4` `C3.mp4` `C4.mp4` が入っています。
12. 最後のセルを実行して、A100 のランタイムを消す。消さないと GPU の枠が残ります。

画の中に文字は入りません。テロップはあとで編集で足します。

## 選んでいるもの

**重みの置き場所。** `マイドライブ/minimax-h3-comfyui/models/` です。生成用ノートはここを ComfyUI に繋ぐだけで、実行中に Hugging Face へ取りに行きません。ダウンロードは CPU ノートの 1 回だけです。

**A100 と fp8 / fp16。** 40GB の A100 は `wan2.1_vace_14B_fp8_scaled.safetensors` を使います。A100 には fp8 の専用演算が無いので、これは計算を速くするためではなく、重さが半分になって載るためです。80GB の A100（と H100 以降）は公式の fp16 を使います。テキストエンコーダは `umt5_xxl_fp8_e4m3fn_scaled.safetensors`、VAE は `wan_2.1_vae.safetensors` です。

**速さ。** 初期値の `fast` は lightx2v の 4 step 蒸留 LoRA（`wan2.1_t2v_14b_lora_rank64_lightx2v_4step.safetensors`）、cfg 1、shift 8、サンプラー `uni_pc` です。VACE 14B は T2V 14B 系なので、この T2V 用 LoRA を使います。CausVid（`Wan21_CausVid_14B_T2V_lora_rank32_v2.safetensors`）は同じ考え方の古い蒸留です。使うときは生成セルの `MODE` を `causvid` にします。`quality` は蒸留を外し、20 step、cfg 5、shift 8 です。cfg 5 は Wan 14B のガイドスケール、shift 8 は ComfyUI の VACE テンプレートに合わせています。

**SageAttention と torch.compile。** 入れば起動時に `--use-sage-attention` を付けます。コンパイルは `--fast fp16_accumulation autotune` です。fp8 の行列積はこの GPU では付けません。入らなかった場合は普通の注意計算のまま続きます。

**TeaCache。** 初期値はオフです。オンにすると Wan2.1 T2V 14B の公開推奨値（`rel_l1_thresh` 0.2、開始 0、終了 1）を使います。4 step の fast と重ねると動きが落ちることがあります。

**画を足す処理。** 初期値はオフです。`USE_UPSCALE` は RealESRGAN x2（`RealESRGAN_x2plus.pth`）で各フレームを 2 倍にします。`USE_RIFE` は RIFE 4.7 で間のフレームを足し、再生速度を上げて尺を保ちます。RIFE の計算は A100（Ampere）向けに bfloat16 です。どちらも VRAM を追加で使います。

**顔。** `FACE_CONSISTENCY` がオンのとき、サクラが映る C2 と C4 だけ参照画像を渡し、プロンプトに参照と同一人物である状態の語を足し、画面上のほうの楕円では制御を少し弱めます（`FACE_PROTECT` の初期値 0.35）。C1 と C3 は人がいないので顔画像を渡しません。猫の顔が溶けるときは 0.35 を下げるか、このスイッチをオフにします。

**LoRA。** `models/loras/sakura_face.safetensors` と `models/loras/dreamcore_style.safetensors` は、自分で置いたときだけ読みます。strength の初期値は 0 で、そのときはノード自体を外します。ログインや支払いが要る LoRA は、CPU ノートの対象にしていません。

**OpenPose と Depth。** 制御 JSON は骨格画像ではなく、ポーズの名前と焦点の往復です。ランナーが棒人間と濃淡を描き、それを VACE の制御動画にします。グラフには `OpenposePreprocessor` と `DepthAnythingPreprocessor` も入っていて、初期値では実行しません。手元の連番画像で取りたいときだけ `PLATE_DIR` にそのフォルダを入れます。Depth の小さなモデルは CPU ノートが Drive の `models/hf-home` に置きます。

**カメラ。** 制御 JSON の移動・回転・手ブレ（1〜2px、不規則）は、制御画像をずらすことで入れます。VACE は Fun Camera 用のカメラ埋め込みを受け取らないので、そちらのモデルは読みません。移動と回転はカットのあいだで 0 から指定値まで進み、手ブレは毎フレームです。

**出力。** Video Helper Suite の `video/h264-mp4`、`yuv420p`、crf 19 です。サイズの初期値は 576×1024 で、これは 9:16 かつ 16 の倍数です。720×1280 と 432×768 も同じ条件を満たします。フレーム数は尺に一番近い 4n+1 です（C1 は 37、C2 は 85、C3 は 73、C4 は 37。fps は制御 JSON の 24）。

## うまくいかないとき

- 「Drive に無い」と出たら、CPU ノートが終わる前に生成ノートを開いています。CPU ノートを先に終わらせます。
- 顔画像が無いと、C2 の直前で止まります。`refs/sakura-face-crop.jpg` を置いて、生成セルだけ再実行できます。
- 起動セルのログは `/content/comfyui.log` です。
- mp4 が Drive に入ったあとに最後のセルを実行します。
