# H3 静止画1枚 → 縦動画

MiniMax H3（`MiniMaxAI/MiniMax-H3`）で、静止画1枚と英語プロンプトから縦 9:16 の mp4 を1本出す。参照動画は要らない。参照画像を外すと、同じ入口で T2VA（文章だけ）になる。

推論の入力は公式の形だけを使う。

- リクエスト JSON は [MiniMax-AI/MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3) `d21241f` の `scripts/readme/reproducible-768p-*.sh` と、README が指す [SGLang cookbook](https://docs.sglang.io/cookbook/diffusion/MiniMax/MiniMax-H3) の `conditions`（`type` / `uri` / `role`）。
- 1枚の静止画は `{"type":"image","uri":"file://...","role":"reference"}`。動画条件は付けない。
- 実行は README がローカル経路として挙げている diffusers の `ModularPipeline`（`workflow="ref2va"` または `"t2va"`）。`MiniMaxH3ImageReference.from_file` で画像を渡す。

LoRA は要らない。公式の推論スクリプトは CFG 蒸留済みの BF16 ベースだけを読む。H3-Context-IR と H3-Regenerate-2K はオープンソースに無い。プロンプトはすでに Context-IR の6節（Ref2VA）または3フィールド（T2VA）で書いてある。

## 15秒を1本で出せるか

出せない見立て。ノートの既定は 6秒 + 9秒。

1. diffusers の `before_encoder.py` は、切り上げた尺が 5秒以上 15秒以下のときだけ通す。15秒は `round(15*24)=360` フレームで、VAE の `17*n+5` に上げると 362 フレーム = 15.083秒になり、拒否される。公式コメントも「346 フレームは 362 に上がって 15.083秒になる」と書いている。合法な最長は 345 フレーム（14.375秒）。
2. 公式の重みは transformer 61.7GB（BF16）+ テキストエンコーダ 62.1GB。80GB 1枚には同時に載らない。公式の対策は `ComponentsManager.enable_auto_cpu_offload`（`memory_reserve_margin="12GB"`）。ホスト RAM が約 140GB 無い Colab では、同じ文書の int8 + group offload（ホスト RAM 約 75GB）を使う。
3. diffusers PR 14371 は、参照画像つき Ref2VA の既定キャンバスが 80GB で OOM だと書いている。参照画像は短辺 2048 で符号化される。通した比較は 512×896、124 フレーム（約 5.2秒）。15秒級（345 フレーム）はその約 2.8倍の列になる。

既定の2本:

| クリップ | タスク | 参照 | 指定秒 | 生成フレーム | キャンバス |
|---|---|---|---|---|---|
| 前半 | T2VA | なし | 6.00秒 | 158（6.583秒） | 768×1344（短辺 768） |
| 後半 | Ref2VA | サクラ静止画1枚 | 9.00秒 | 226（9.417秒） | 352×640（短辺 352） |

9秒の画が小さいのは、上の「80GB で通った」トークン数に収めるため。ffmpeg が各クリップを 6.00秒と 9.00秒で切り、1080×1920 に伸ばして `orbis01.mp4`（15.00秒）にする。切る前の mp4 も同じフォルダに残る。

`--force-one-shot` は 345 フレーム（14.375秒）を 288×512 で試す経路。ノートはこれを使わない。

## 人間がやること

1. Colab でノートを開く。  
   https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-still-to-video-7cb8/h3-runner/minimax_h3_still.ipynb
2. ランタイムのタイプを **A100 GPU** にする。40GB（表示は 39.5GB 前後）でよい。公式の int8 + group offload は 24〜32GB のカード向けで、40GB はその上。ホスト RAM はハイメモリ（約 75GB 以上。83GB 前後で足りる）。140GB 以上あるマシンなら自動で BF16 offload になる。24GB 未満は止まる。
3. [MiniMaxAI/MiniMax-H3](https://huggingface.co/MiniMaxAI/MiniMax-H3) のライセンスを自分の Hugging Face アカウントで開く。ダウンロードが 401 になるときは、Colab のシークレットに `HF_TOKEN` を入れる。ノートは値を表示しない。Git には書かない。
4. ノートを上から順に実行する。プロンプトも静止画もノートがリポジトリから取る。
5. 完成ファイルは Google Drive の `マイドライブ/h3-runner/output/orbis01.mp4`。

所要時間の公式実測は、A100 1枚には無い。重みは T2VA 用と Ref2VA 用で transformer が各 61.7GB、テキストエンコーダが 62.1GB。初回は Drive の `h3-runner/hf-cache` へこのダウンロードが大半になる。生成は 50 step × 2本で、offload がステップごとに重みを出し入れする。SGLang が 4×H200・5秒・50 step・offload なしで出している 75秒より長くなる。1本が数分で終わる前提にはしない。2回目以降はキャッシュを使うのでダウンロードは無い。

## コマンド

ノートと同じ2本:

```bash
python h3-runner/run_h3.py --preset orbis01 --out-dir /content/drive/MyDrive/h3-runner/output --seed 0
```

同じ入口で1本だけ。秒数は 4〜15。4秒と、切り上げが 15秒を超える 15秒は diffusers が拒否する。縦横比の既定は 9:16。`--width` と `--height` は 32 の倍数で両方指定する。

```bash
python h3-runner/run_h3.py \
  --task ref2va \
  --prompt-file h3-runner/prompts/orbis01_ref2va_9s.txt \
  --image h3-runner/assets/sakura-ref.jpg \
  --duration 9 --aspect 9:16 --seed 0 \
  --out /tmp/sakura_9s.mp4

python h3-runner/run_h3.py \
  --task t2va \
  --prompt-file h3-runner/prompts/orbis01_t2va_6s.txt \
  --duration 6 --aspect 9:16 --seed 0 \
  --out /tmp/water_6s.mp4
```

計画だけ見る（GPU も重みも要らない）:

```bash
python h3-runner/run_h3.py --preset orbis01 --dry-run --vram-gb 80 --host-ram-gb 83
```

テスト:

```bash
python -m unittest h3-runner/tests/test_planner.py
```
