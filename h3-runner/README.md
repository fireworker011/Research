# H3 静止画1枚 → 縦動画（ノンアダルト）

アダルトの LoRA スタジオと病棟ノートはこのツリーに無い。プランの入口は `minimax_h3_studio_bot.ipynb`。このノートは FL2VA の生成側。

MiniMax H3（`MiniMaxAI/MiniMax-H3`）で、静止画1枚と英語プロンプトから縦 9:16 の mp4 を1本出す。参照動画は要らない。

既定の2本はどちらも FL2VA。静止画はパイプラインの `image=` に渡し、最初のコマにする。公式リクエストの conditions は `role=keyframe`, `frame_index=0`（`scripts/readme/reproducible-768p-fl2va-request.sh`）。Ref2VA（`references=`、`role=reference`）は `--task ref2va` で残している。

推論の入力は公式の形だけを使う。

- リクエスト JSON は [MiniMax-AI/MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3) `d21241f` の `scripts/readme/reproducible-768p-*.sh` と、README が指す [SGLang cookbook](https://docs.sglang.io/cookbook/diffusion/MiniMax/MiniMax-H3) の `conditions`。
- 実行は diffusers の `ModularPipeline`（固定コミット `5ff8e59`。`MiniMaxH3LoraLoaderMixin` が ComfyUI キー変換と `adapter_name` を持つ）。`workflow` は `fl2va` / `t2va` / `ref2va`。

## 高速化の構成

前の G4（RTX PRO 6000 96GB）は T2VA 6秒 + Ref2VA 9秒、各 49 ステップ、bf16 と `enable_auto_cpu_offload` で約 43 分だった。既定は次にする。質は同じ seed の mp4 を見て判断する。新しい所要時間は、この GPU の公式実測としては書いていない。

| 項目 | 値 |
|---|---|
| タスク | FL2VA が2本（6秒と9秒）。どちらもサクラの静止画を最初のコマにする |
| steps | 9。`MiniMaxH3Scheduler` は `linspace(1, 0, steps)` で終点 0 を含むので、モデル評価は 8 回 |
| video shift | 6（`--video-shift`。既定 6）。audio shift は 3 |
| offload | bf16 のとき `enable_auto_cpu_offload`（margin 12GB）。LoRA の融合はその前 |
| LoRA | bf16 だけ。`--lora パス:強さ` を繰り返す。`set_adapters` → `fuse_lora` → `unload_lora_weights`。融合しないと静止画1枚あたりおおよそ 9〜13% 増える |
| int8 | LoRA は無効。shift だけ適用する |
| FL2V LoRA の載せ先 | `transformer`。`load_into_transformer_ref=True` は `ref2va` のときだけ。FL2V LoRA を `transformer_ref` に載せると劣化する |

Turbo は [lightx2v/Minimax-h3-Turbo](https://huggingface.co/lightx2v/Minimax-h3-Turbo) の `minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors`（ComfyUI bf16。ライセンスはリポジトリの Apache-2.0）。強さ 1.0。学習設定は 768p、video shift 6、audio shift 3、評価 8 回。

比較用に足す LoRA（ノートの「B. 比較テスト」）:

| 記号 | 中身 | 強さ |
|---|---|---|
| A | 既存の `orbis01_6s.mp4`（作り直さない） | — |
| B | FL2VA + Turbo | 1.0 |
| C | B + Combat BASE V2（`H3_Combat_V2.safetensors`） | 0.7 |
| D | C + Motion Continuity Repair V2 | 0.6 |
| D' | B + Motion Continuity Repair V2（Combat 無し） | 0.6 |

Combat BASE V2 は **BUNNY（作者 FourBunny）**。ファイルは Hugging Face `JOKER141/MiniMax-H3-Combat-Base-V2` の `H3_Combat_V2.safetensors`。Civitai の `combat_base_v2.safetensors` は同じ LoRA の別名なので、このツリーでは落とさない。

Motion Continuity Repair V2 の取得元は [JOKER141/MiniMax-H3-General-Motion-Continuity-Repair](https://huggingface.co/JOKER141/MiniMax-H3-General-Motion-Continuity-Repair) の `Motion_Repair_V2.safetensors`（base_model `MiniMaxAI/MiniMax-H3`、lora、2026-09-28 更新）。カードの名前は BUNNY Motion Repair V2。V1 の `Motion_Repair.safetensors` は置かない。Civitai 3366092 は使わない。Repair を使った動画には BUNNY と、配布の JOKER141 を書く。

ヘッダ（テンソル本体は読んでいない）: 416 キー、すべて `diffusion_model.blocks.*` の `lora_A` / `lora_B`。AdaLN キーは無く、入力幅 8 ではない。`__metadata__.software` は ai-toolkit。ComfyUI の `.alpha` も `lora_down` も無い。diffusers `5ff8e59` の `load_lora_weights` は `diffusion_model.` で始まるキーを `_convert_non_diffusers_minimax_h3_lora_to_diffusers` に渡すので、事前の変換ファイルは作らない。準備セルは同じ拒否（AdaLN 入力幅 8）と、このキー形の確認を、置いたファイルに対して行う。

AdaLN の入力幅が 8 の safetensors（Pruned 学習）は読む前に拒否する。公開 BF16 の AdaLN 入力は 2688。ヘッダのキーと shape だけを見て、テンソル本体は読まない。

## 15秒を1本で出せるか

出せない見立て。ノートの既定は FL2VA の 6秒 + 9秒。

1. diffusers の `before_encoder.py` は、切り上げた尺が 5秒以上 15秒以下のときだけ通す。15秒は `round(15*24)=360` フレームで、VAE の `17*n+5` に上げると 362 フレーム = 15.083秒になり、拒否される。合法な最長は 345 フレーム（14.375秒）。
2. 公式の重みは transformer 61.7GB（BF16）+ テキストエンコーダ 62.1GB。80GB 1枚には同時に載らない。公式の対策は `ComponentsManager.enable_auto_cpu_offload`（`memory_reserve_margin="12GB"`）。ホスト RAM が約 140GB 無いときは、同じ文書の int8 + group offload（ホスト RAM 約 75GB）を使う。その経路では LoRA を載せない。
3. Ref2VA は参照画像を短辺 2048 で符号化する。diffusers PR 14371 が 80GB で通せたと書いているのは 512×896、124 フレーム。FL2VA はその参照を使わず、静止画を目標キャンバスへ伸ばす。キャンバスは T2VA と同じトークン予算（124 フレーム・768p の 1.35 倍まで）。

既定の2本:

| クリップ | タスク | 静止画 | 指定秒 | 生成フレーム | キャンバス |
|---|---|---|---|---|---|
| 前半 | FL2VA | 最初のコマ | 6.00秒 | 158（6.583秒） | 768×1344（短辺 768） |
| 後半 | FL2VA | 最初のコマ | 9.00秒 | 226（9.417秒） | 640×1152（短辺 656） |

書き出しは `orbis01_fl2va_6s.mp4` と `orbis01_fl2va_9s.mp4`。既存の `orbis01_6s.mp4` は上書きしない（比較の A）。ffmpeg が各クリップを 6.00秒と 9.00秒で切り、1080×1920 に伸ばして `orbis01.mp4`（15.00秒）にする。

`--force-one-shot` は Ref2VA の 345 フレーム（14.375秒）を予算内の短辺で試す経路。ノートはこれを使わない。

## 人間がやること

ノート: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-sfw-colab-6dc5/h3-runner/minimax_h3_still.ipynb

Drive のアカウントは毎回選ぶ。ノートの Drive セルに、その回のマイドライブの中のフォルダ名を書く。既定は重み `h3-weights`、完成 mp4 `h3-runner/output`。前回のマウントは次の VM に残らない。

[MiniMaxAI/MiniMax-H3](https://huggingface.co/MiniMaxAI/MiniMax-H3) のライセンスを自分のアカウントで開く。401 のときだけ Colab のシークレット `HF_TOKEN` を入れる。ノートは値を表示しない。

既定の FL2VA が置くのは text_encoder + transformer + vae + audio_vae + tokenizer/processor で、プレビューの合計は **144.1GB**。`transformer_ref` は `--task ref2va` のときだけ足す。T2VA と Ref2VA を両方置いた合計はこれまでどおり **210.3GB**。`FL2VA/` と `Ref2VA/`（各 144.1GB の Comfy チェックポイント）は落とさない。

ページの先頭に手順がある。CPU で 1-1 から 1-4（Drive、プログラム、道具、重み）。そのあとランタイムを G4 に変え、2-1 と 2-2（Drive をもう一度、動画を焼く）。一番下の比較は本編ではない。

重みは Hugging Face。Turbo の ComfyUI bf16、Repair の `Motion_Repair_V2.safetensors`、Combat の `H3_Combat_V2.safetensors`。`HF_TOKEN` はライセンスで 401 のときだけ、セルには書かない。

## コマンド

重みの準備（CPU。GPU 不要）:

```bash
python h3-runner/run_h3.py --preset orbis01 \
  --cache-dir /content/drive/MyDrive/h3-weights \
  --out-dir /content/drive/MyDrive/h3-runner/output \
  --prepare-weights --vram-gb 95 --host-ram-gb 176.9
```

LoRA は同じ CPU セルが `h3_runner.loras.prepare_fast_loras` で `h3-weights/loras/` に置く。

生成（ダウンロードしない。bf16。Turbo を融合する）:

```bash
python h3-runner/run_h3.py --preset orbis01 \
  --cache-dir /content/drive/MyDrive/h3-weights \
  --out-dir /content/drive/MyDrive/h3-runner/output \
  --seed 0 --steps 9 --video-shift 6 \
  --lora /content/drive/MyDrive/h3-weights/loras/minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors:1.0
```

6秒の比較1本（ノートの B と同じ）:

```bash
python h3-runner/run_h3.py \
  --task fl2va \
  --prompt-file h3-runner/prompts/orbis01_t2va_6s.txt \
  --image h3-runner/assets/sakura-ref.jpg \
  --duration 6 --width 768 --height 1344 --seed 0 --steps 9 --video-shift 6 \
  --lora /content/drive/MyDrive/h3-weights/loras/minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors:1.0 \
  --lora /content/drive/MyDrive/h3-weights/loras/H3_Combat_V2.safetensors:0.7 \
  --out /tmp/test_c.mp4
```

Ref2VA は残している。秒数は 4〜15。`--width` と `--height` は 32 の倍数で両方指定する。

```bash
python h3-runner/run_h3.py \
  --task ref2va \
  --prompt-file h3-runner/prompts/orbis01_ref2va_9s.txt \
  --image h3-runner/assets/sakura-ref.jpg \
  --duration 9 --aspect 9:16 --seed 0 \
  --out /tmp/sakura_9s.mp4
```

計画だけ見る（GPU も重みも要らない）:

```bash
python h3-runner/run_h3.py --preset orbis01 --dry-run --vram-gb 95 --host-ram-gb 176.9
```

テスト（CPU。GPU も diffusers も要らない）:

```bash
python -m unittest h3-runner/tests/test_planner.py
```
