# MiniMax H3 の仕様（ほかの AI 向け）

この文書は、このリポジトリの MiniMax H3 を Colab で動かすための正本です。数字はコードとノートに書いてあるものだけです。測っていない秒数は書かないでください。

コードの基準はブランチ `cursor/sakura-five-stills-80fd` のコミット `f1911062` です。この仕様書はそのコミットのあとに足しています。実装と食い違ったら、この文書ではなくコードを正にしてください。

## リンク

- リポジトリ: https://github.com/fireworker011/Research
- ブランチ: https://github.com/fireworker011/Research/tree/cursor/sakura-five-stills-80fd
- プルリクエスト: https://github.com/fireworker011/Research/pull/304
- Colab（ブランチの先端。動くと中身が変わる）: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/sakura-five-stills-80fd/minimax_h3_comfyui_colab.ipynb
- Colab（`f1911062` に固定。ステージングと実測タイマーまで）: https://colab.research.google.com/github/fireworker011/Research/blob/f191106281887077389c32b8a057eb26d6f83581/minimax_h3_comfyui_colab.ipynb
- 計画だけのノート: https://github.com/fireworker011/Research/blob/cursor/sakura-five-stills-80fd/minimax_h3_live_remake.ipynb
- 公式チュートリアル: https://docs.comfy.org/tutorials/video/minimax/minimax-h3
- 公式の重み: https://huggingface.co/Comfy-Org/MiniMax-H3
- Drive の models フォルダ ID: `1zd4IaS-pw1RJrx4TaGDGgS1ZpBsjeVRK`
- Drive 上のパス: `/content/drive/MyDrive/minimax-h3-comfyui/models`
- ノートが指定する Drive アカウント: `ys73497349@gmail.com`
- さくら刀の出力先: `/content/drive/MyDrive/動画倉庫/00_確認待ち/sakura-sword`
- 参照動画の計測元（Drive ファイル ID `1G61IM9tj4eecFi_lDntB1ux_ny0yhle8`）: 244 フレーム、24fps、1280×714。パスは `/content/drive/MyDrive/動画倉庫/ネタBOX/QT0eqhCA1_tQ2Y-FcRGv-_mF7FksnCdXu7K8HSoIJ4s.mp4`

公開、投稿、契約、課金の操作はこの仕様の外です。

## このチェックアウトでできること

生成する本体は `minimax_h3_comfyui_colab.ipynb` です。ComfyUI 0.30.0 以降を Colab の GPU に置き、重みは Drive から繋ぎます。ノート先頭の記載では、モデル一式のディスク目安は約 42.5GB です。推奨 GPU は L4 か A100 で、無料の T4 は遅いと書いてあります。実際の GPU 名はこのリポジトリにありません。セル 0 の `nvidia-smi` が正です。

経路は二つです。

- **FL2VA**（いまのさくら刀）。静止画の最初と最後だけ。元動画は渡しません。ノードは `MiniMaxH3ImageToVideo`。本体は `minimax_h3_fl2va_pruned_int8_convrot.safetensors`。セル 5c。
- **Ref2VA / R2V**。参照動画と静止画。ノードは `MiniMaxH3ReferenceToVideo`。本体は `minimax_h3_ref2va_pruned_int8_convrot.safetensors`。計画は `h3/live_remake.py` と `h3/sakura_clip.py`。span の投入はセル 5b。さくら刀の現行生成では使いません。

`minimax_h3_live_remake.ipynb` と `h3/reproduce.py` は計画とプロンプトまでです。生成キューは投げません。既定は steps 20。4step LoRA は明示したときだけです。

`h3/desk.py` の fast_motion や combat_motion などは `present=False` です。実体の `colab/h3_studio.py` はこのチェックアウトにありません。6 秒で 158 フレーム、9 秒で 640×1152、Turbo steps 9、という記述はそちらの仕様であり、セル 5c は使いません。

`wan22_i2v_lightx2v_colab.ipynb` は WAN 2.2 です。H3 とは別系統です。ノートには、97 フレームに約 30GB VRAM と書いてあります。`Lora_Trainer_XL.ipynb` は SDXL の LoRA 学習です。この動画生成には繋ぎません。

## やってはいけないこと

- 本体、VAE、Combat、Motion Repair を、Drive に無いからといって新たに落とさない。例外はセル 3 が、テキストエンコーダが無い、またはサイズが 15,687,142,551 バイトでないときだけ、公式の resolve URL からその 1 ファイルを取る場合です。
- `fp8` は拒否です。Drive にある本体は int8 です。
- 8step の Turbo LoRA を付けたまま steps だけ 20 にしない。Turbo と Combat、Turbo と Motion Repair を同じサンプラに積まない。
- 長さを 17k+5 以外にしない。124 未満と 345 超、362 は拒否です。
- 横の生成サイズを 1920×1080 にしない。この環境の横 16:9 は 1344×768（768P）です。縦は 768×1344 です。
- 既存の mp4 を上書きしない。
- セル 5b（span-01）と、その下の localtunnel 用 5b は、頼まれない限り実行しない。
- セル 5 の URL 待ちで止まっても、`OK: ComfyUI listening` のあとならサーバーは起動済みです。セルを止めて 5c に進んでよい。止めてもサーバーは落ちない実装です。
- 測っていない秒数、料金、成果を書かない。

## 実行順

ランタイムは GPU。

1. セル 0。GPU 名と VRAM、ディスク。
2. セル 1。Drive をマウントする。
3. セル 2。ComfyUI を `git clone --depth 1` する。コミットは固定していない。
4. セル 3。`MODE` の既定は `r2v`。Drive のモデルフォルダを ComfyUI に繋ぐ。`fp8` は止める。
5. セル 3b は計画の表示だけで、キューを投げない。実行しなくてよい。
6. セル 4。公式ワークフロー JSON を置く。
7. セル 5。ComfyUI を 8188 で起動する。
8. セル 5c。さくら刀を 1 本投げる。

3b と 5b は実行しない。

## セル 5（起動）

`EXTRA_ARGS` の既定は `auto` です。

- VRAM が 75GiB（`75 * 1024**3` バイト）以上のときだけ `--highvram`。
- 未満は引数なし。動的 VRAM のまま。40GB 級はこちらです。
- フォームで `""` を選ぶと、VRAM が大きくても引数なしです。`--lowvram` などを明示したときはその文字列を使います。

起動前に GPU 名、VRAM の GiB とバイト、RAM の総量と空き、`/content` の空きを出します。実装は `h3/fl2va_runtime.py` の `read_hardware` と `vram_launch_arg` です。

`--normalvram` は、この系統の ComfyUI では廃止されています。渡さないでください。

URL が 15 秒で来なければ、セルはそこで終わります。生成そのものは 127.0.0.1:8188 です。

## セル 5c（FL2VA）

フォームは次です。

- `MODE`: `fast_8step` または `quality_20step`
- `ACTION`: `一刀`、`連撃`、`突進`、`旋回`
- `FRAMES`: `260` または `243`

`fast_8step` は `minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors` を強さ 1、steps 8 だけです。`quality_20step` は LoRA ノードを付けず、steps 20 だけです。待ちの上限は 8step が 90 分、20step が 225 分です。これは打ち切りであり、実測時間ではありません。履歴の確認は 2 秒間隔です。

`FRAMES` は投入前に `124 <= frames <= 345` かつ `(frames - 5) % 17 == 0` を検査します。260 は 244 フレーム以上で最小の合法長です。243 は `17*14+5` で、元より 1 フレーム短い合法長です。既定は 260 です。

画面は 1344×768、24fps。サンプラは `res_multistep`、scheduler は `simple`、denoise は 1 です。最初の絵は `h3/stills/sakura-16x9-open.jpg`（1792×1008）。最後の絵は `h3/stills/sakura-16x9-yokai-end.jpg`（1792×1008）。セルはブランチからこの 2 枚を取ります。生成サイズは静止画のピクセル数ではなく 1344×768 です。

速度の指定はプロンプトに書いてあります。ダッシュから最後の一刀まで落とさない。スロー、ヒットストップ、一時停止は入れない。終わりの一瞬だけ最後の絵（妖怪と「祝千三百」）に合わせます。元動画のコマは渡しません。

出力名は既存ファイルを上書きしません。

| ACTION | fast_8step | quality_20step |
|---|---|---|
| 一刀 | `sakura-fl2va-speed8.mp4` | `sakura-fl2va-speed20.mp4` |
| 連撃 | `sakura-fl2va-chain8.mp4` | `sakura-fl2va-chain20.mp4` |
| 突進 | `sakura-fl2va-rush8.mp4` | `sakura-fl2va-rush20.mp4` |
| 旋回 | `sakura-fl2va-arc8.mp4` | `sakura-fl2va-arc20.mp4` |

R2V 時代の `sakura-sword.mp4` と `sakura-sword_with-audio.mp4` は別ファイルです。

### ローカルへのコピー

セル 5c は Drive の約 42.5GB をまとめてコピーしません。次の 5 ファイルだけを `/content/local_models` に置き、ComfyUI の `models/` からそこへファイル単位でリンクします。`minimax_h3_ref2va_pruned_int8_convrot.safetensors` はコピーしません。Drive へのリンクのままです。

優先順は次です。

1. `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`（15,687,142,551 バイト）
2. `vae/minimax_h3_video_vae_fp16.safetensors`
3. `vae/minimax_h3_audio_vae_fp32.safetensors`
4. `diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors`
5. `loras/minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors`

コピー後も 15GiB 空くときだけ 5 つ全部を置きます。足りないときは上の順で入るものだけ置き、残りは Drive のままです。コピー秒数をログに出します。同じサイズのファイルが既にあればコピーし直さず「既存を使う」と出します。

動画 VAE の公式名は `minimax_h3_video_vae_int8_convrot.safetensors` です。Drive にあるのは fp16 の方なので、セルは fp16 を使います。音声 VAE もグラフに入り、映像のあとでデコードします。

完了時に次の 5 行を出します。ログに行が無い段階は「未計測」です。

1. テキストエンコーダのロードとエンコード
2. 拡散ループのロードと推論、および `s/it`
3. 動画 VAE のデコード
4. 音声 VAE のデコード
5. キュー投入からファイル保存までの実測秒

Comfy が `Prompt executed in ... seconds` を出したときは、その秒も別行で出します。

## 共通のフレームとサンプラ

実装は `h3/live_remake.py` です。

- fps は 24。
- 合法な長さは `17k+5`。最短 124 フレーム（5.167 秒）。15 秒未満の最後は 345 フレーム（14.375 秒）。362 は拒否。
- 244 フレームの次の合法長は 260 フレーム（10.833 秒）。差は 16 フレーム、0.667 秒。
- 横 1344×768、縦 768×1344。解像度の名前は 768P。
- サンプラ `res_multistep`、scheduler `simple`、denoise 1。
- テキストエンコーダの type は `minimax`。ファイルは `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`。
- 参照画像は R2V で 9 枚まで。タグは `<Picture i>`、`<Video k>`、`<Audio j>`。

台本の時刻は、15 秒表記の切れ目 `(0, 1, 4, 7, 10, 12)` を、244/24 秒へ縮めたものです。`h3/sakura_clip.py` の `scaled_marks` が計算します。FL2VA の最後の区間の終わりは、選んだフレーム数 / 24 です。260 なら 10.833 秒、243 なら 10.125 秒です。

## R2V のさくら計画（セル 5c では使わない）

`h3/sakura_clip.py` は生成しません。静止画 5 枚はネタBOX の次のファイル名です。

- `sakura-01-face.jpg` 顔と髪
- `sakura-02-front.jpg` 正面
- `sakura-03-back.jpg` 後ろ
- `sakura-04-sword.jpg` 刀と寺
- `sakura-05-night.jpg` 衣装だけ。夜空は場所にしない

LoRA は `Motion_Repair_V2.safetensors` 強さ 0.6 の次に `H3_Combat_V2.safetensors` 強さ 0.7 です。トリガーは `prfight2, prfin1` です。steps は 20。4step の `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` はオフです。要求フレームは 260、画面は 1344×768 です。

セル 5b の span も steps 20、LoRA なし、1344×768 です。長さが 124 未満なら拒否します。出力名は `span-01.mp4` のような形で、既存があれば上書きしません。

## コードの対応

| 役割 | ファイル |
|---|---|
| フレーム格子、R2V の定数、計測 | `h3/live_remake.py` |
| Drive 接続。実体の重みファイルがあるディレクトリは消さない。シンボリックリンクだけの重ねがけは Drive へ戻せる | `h3/drive_models.py` |
| さくら R2V の計画。生成しない | `h3/sakura_clip.py` |
| R2V グラフと FL2VA グラフ、台本 4 本、モード排他 | `h3/sakura_queue.py` |
| 5 ファイルのローカルコピー、VRAM 引数、フェーズの読み取り | `h3/fl2va_runtime.py` |
| span を 1 本にするグラフ | `h3/span_queue.py` |
| 再現プロンプト。キューは投げない | `h3/reproduce.py` |
| レーン一覧。`present=True` は live_remake と reproduce だけ | `h3/desk.py` |
| 最初と最後の静止画 | `h3/stills/sakura-16x9-open.jpg`、`h3/stills/sakura-16x9-yokai-end.jpg` |

セル 3 が取る `drive_models.py` のブランチは `cursor/h3-live-remake-on-minimax-80fd` です。セル 3b とセル 5 とセル 5c が取る Python は `cursor/sakura-five-stills-80fd` です。セル 5b は親ブランチの span 用です。

テストは次です。

```bash
python3 -m unittest h3.test_fl2va_runtime h3.test_sakura_queue h3.test_sakura_clip h3.test_drive_models h3.test_span_queue h3.test_live_remake h3.test_reproduce
```

## まだこのリポジトリに無いもの

- セル 0 の実機の GPU 名と VRAM。
- 5 ファイルのコピーに実際にかかった秒と、Drive のまま残ったファイル名。
- フェーズ別の実測秒。ログの文面がパーサと違うと「未計測」になります。
- 260 フレームの 8step と 20step が、その GPU で何秒だったか。
- 速度を落とさないプロンプトで、途中の減速が消えたかの目視。
- 一刀以外の 3 台本の生成結果。
- 768P より上の解像度。このノードの横画面は 1344×768 です。
