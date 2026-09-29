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

9秒の画が小さいのは、上の「80GB で通った」トークン数に収めるため。95GB 級でも広げない。VRAM 比でキャンバスを上げる式は公式に無い。計画のセルがその理由を出す。ffmpeg が各クリップを 6.00秒と 9.00秒で切り、1080×1920 に伸ばして `orbis01.mp4`（15.00秒）にする。切る前の mp4 も同じフォルダに残る。

`--force-one-shot` は 345 フレーム（14.375秒）を 288×512 で試す経路。ノートはこれを使わない。

## 人間がやること

ノート: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-still-to-video-7cb8/h3-runner/minimax_h3_still.ipynb

Drive は **fireworker06@gmail.com** でマウントする。重みは `マイドライブ/h3-weights/MiniMax-H3`。完成 mp4 は `マイドライブ/h3-runner/output/orbis01.mp4`。

[MiniMaxAI/MiniMax-H3](https://huggingface.co/MiniMaxAI/MiniMax-H3) のライセンスを自分のアカウントで開く。401 のときだけ Colab のシークレット `HF_TOKEN` を入れる。ノートは値を表示しない。

Hugging Face の tree API で、T2VA と Ref2VA を両方置いた合計は **210.3GB**（text_encoder 66.73 + transformer 66.28 + transformer_ref 66.28 + vae 10.42 + audio_vae 0.61 + tokenizer/processor）。ダウンロード中は未完了シャード最大 5.1GB が足されて約 215.4GB。`FL2VA/` と `Ref2VA/`（各 144.1GB）は落とさない。空きが足りなければ準備セルが不足分を出して止まる。ゴミ箱を空にするか、大きなファイルを移してからやり直す。G4 では落とさない。

### A. CPU ランタイム（GPU なし）

1. ランタイムのタイプを **CPU** にする。
2. 「A. Drive」セル。空き容量が出る。
3. 「A. リポジトリ」セル。パスは `/content/Research/h3-runner/run_h3.py`。
4. 「A. パッケージ」セル。`huggingface_hub` だけ。
5. 「A. 重み準備」セル。無ければ Drive に一度落とす。揃っていれば落とさない。

### B. G4（RTX PRO 6000）

1. ランタイムのタイプを **G4 GPU** にする。CPU とは別の VM なので、Drive とリポジトリはここでも取る。
2. 「B. 準備」セル。Drive、`torchao==0.18.0`（Colab の torch は置き換えない）、リポジトリ。
3. 「B. 生成」セルだけが生成する。最初から結合までこの1セル。Drive から直接読み、ダウンロードしない。`orbis01_6s.mp4` が Drive にあれば T2VA をスキップして Ref2VA から続ける。

切れたときは B の2セルを上からやり直す。6秒が保存済みならそこは走らない。

所要時間の公式実測は、この GPU には無い。生成は 50 step × 最大2本で、offload がステップごとに重みを出し入れする。SGLang が 4×H200・5秒・50 step・offload なしで出している 75秒より長くなる。1本が数分で終わる前提にはしない。重みの初回ダウンロードは CPU 側で、G4 の時間には入れない。

生成は Drive のスナップショットを直接読む。CPU と G4 は別 VM なので、G4 のローカルディスクへ先に置いておくことはできない。G4 上でローカルへコピーしてから読むと、Drive からの読みに書き込みと再読みが足される。読み込み後の offload はホスト RAM（G4 実測 176.9GB。bf16 の公式目安は約 140GB）に置く。

## コマンド

重みの準備（CPU。GPU 不要）:

```bash
python h3-runner/run_h3.py --preset orbis01 \
  --cache-dir /content/drive/MyDrive/h3-weights \
  --out-dir /content/drive/MyDrive/h3-runner/output \
  --prepare-weights --vram-gb 95 --host-ram-gb 176.9
```

生成（ダウンロードしない）:

```bash
python h3-runner/run_h3.py --preset orbis01 \
  --cache-dir /content/drive/MyDrive/h3-weights \
  --out-dir /content/drive/MyDrive/h3-runner/output --seed 0
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
