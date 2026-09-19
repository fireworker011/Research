# Qwen Image Edit NSFW 引き継ぎ（画像編集 Colab のみ）

GitHub のこのレーンのフォルダは **`qwen-image-edit-nsfw/`**。Drive と同じ名前。H3 動画の `h3-lora-studio/` に混ぜるな。JPG はここに入れない。

## 新規チャットに貼る文

```
Qwen Image Edit NSFW（画像編集 Colab）を続ける。H3 動画は別チャットで引き継ぎ済み。触るな。Naomiichi。

まず読め:
- `qwen-image-edit-nsfw/HANDOVER.md`
- `colab/qwen_image_edit_nsfw.py`
- `colab/_write_qwen_edit_nb.py`

作業ブランチ: `cursor/h3-anal-stories-f112` だけ。新枝禁止。PR #138 は draft のままマージするな。
HEAD: c564f3b h3: Qwen Edit Colab を Mk1227 Space と同じ AIO+FP8 環境にする
Colab: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-anal-stories-f112/qwen_image_edit_nsfw.ipynb

目的: 元画像の顔と画風は変えない。変えてよいのは服・姿勢・場所・行為。
これは i2i（Picture 1＝元画像）。t2i ではない。任意で顔・画風の参照（Picture 2）。
Drive の空きは 2GB で足りる（JPG だけ）。重みは Colab 約70GB（2511 + AIO 28GB）。H3 の 21GB 参照土台は不要。
GPU は A100（40/80）か H100。L4 は offload。T4 は不可。
基本フタナリ（玉なし・マンコあり・竿20cm）。男禁止。成人21+。実写の他人は入れるな。JPGはGitに入れるな。
ipynb は手で直すな。`python3 colab/_write_qwen_edit_nb.py`。H3 スタジオと同時に動かすな。
JSON物語（clinic/cafe/sales含む）は触るな。HQ dump / hq-instruct / Threads cron は触るな。
```

## フォルダ

| 場所 | 用途 |
|---|---|
| **`qwen-image-edit-nsfw/`** | GitHub の引き継ぎ。この `HANDOVER.md` だけ |
| `colab/` | 本体と writer とテスト |
| repo 直下 `qwen_image_edit_nsfw.ipynb` | Colab バッジ先 |
| Drive `MyDrive/qwen-image-edit-nsfw/` | 実ファイル。`input/` と `output/` |

## リンク

- Colab: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-anal-stories-f112/qwen_image_edit_nsfw.ipynb
- 枝: `cursor/h3-anal-stories-f112`
- PR: https://github.com/fireworker011/Research/pull/138 draft vs `cursor/h3-cabin-flow-f112`。マージ禁止
- 版は動画側の `h3-20260914-anal-18` のまま（このノートは版を増やしていない）

## 何をするノートか

起点の静止画を **Qwen Image Edit** で直す。H3 動画ノート（`minimax_h3_lora_studio.ipynb`）とは別ランタイム。

Mk1227 / ayooo123 Space の **公開設定どおり** に Colab へ載せる（コンパイル済み `app.so` はコピーしない）。

Space 本体（`Mk1227/Qwen-Image-Edit-NSFW` `.env.example`）と同じもの:

- 土台 `Qwen/Qwen-Image-Edit-2511`
- AIO 単一ファイル `Phr00t/Qwen-Image-Edit-Rapid-AIO` の `v23/Qwen-Rapid-AIO-NSFW-v23.safetensors` を注入
- FP8 quant オン（Colab は `torchao>=0.16.0`。Space `.env` の `0.11.0` は今の git+diffusers で `FqnToConfig` が無く②が落ちる）、A100 は GPU 常駐、24GB 級は `model_cpu_offload`
- 4step / guidance 1.0 / サイズ **auto** / rewrite **既定オン**（72B VL。HF_TOKEN が無いときは入力文のまま）
- 追加 LoRA なし（NSFW は AIO に焼き込み）。②の追加LoRAはオフのまま
- FlowMatch `SCHED_*`（exponential `log(3)` / 8192）
- pip は `git+https://github.com/huggingface/diffusers.git`

H3 側で足しているもの（Space UI には無い）:

- クイックはフタナリに差し替え。`Realistic nude body` は消す
- 短い `FACE_KEEP`
- ②で追加LoRAをオンにしたときだけ jt65 Fast2（顔が別の人になりやすい）

ZeroGPU の `/infer` 経路は別: `h3-lora-studio/scripts/qwen_edit_nsfw.py`。Colab GPU 経路と混ぜない。

保存先は Drive `qwen-image-edit-nsfw/output`。Git に JPG を入れない。

**i2i。** `QwenImageEditPlusPipeline` に Picture 1（編集する元画像）を渡す。文章だけからは描かない。任意で Picture 2＝顔と画風の参照（同じ人物の別カット）。ファイル名に `photoreal` / `実写` があるとスキップ。

### Drive の空き

| 置くもの | 場所 | 目安 |
|---|---|---|
| 元画像・出力 JPG | Drive `qwen-image-edit-nsfw/input` と `output` | **2GB あれば足りる** |
| 重み（2511 + AIO 28.4GB + text encoder） | **Colab ディスク** HuggingFace キャッシュ | 約70GB。Drive には載せない |

H3 スタジオの参照土台（R2V 約21GB）は **不要**。このノートは Drive にモデルを置かない。

HF ZeroGPU 経由の別経路は `h3-lora-studio/scripts/qwen_edit_nsfw.py`（本命 Mk1227 `/infer`）。Colab GPU 経路と混ぜない。

## 必須ロック

毎回のプロンプトに短い keep-face は入る。長い IDENTITY LOCK 文は載せるな（t2i になる）。

| 固定 | 内容 |
|---|---|
| 顔 | `FACE_KEEP`。同一人物・同一顔・髪。入れ替え禁止 |
| 画風 | `STYLE_PRESETS`。短い1文。変換しない。既定 **入力のまま** |
| 参照 | 任意。`REF_FACE`。Picture 2 が顔と画風 |
| フタナリ | 玉なし・マンコあり・竿20cm。男禁止 |
| 服抜き既定 | 姿勢・場所も維持。服だけ |
| 行為 | 姿勢・場所・行為は変えてよい。顔と画風は維持 |

「リアルに」は体液・糞の質感。画風を実写へ変換するな。

## ③クイックプロンプト

既定: `服抜きフタナリ（既定）`

Space と同じ12個: 服を脱ぐ / ウェットシャワー / レースランジェリー / ビキニ / 濡れたTシャツ / フェラチオの視点 / セルフタッチ / 宣教師 / カウガール / 乳房プレイ / フェイシャル / 肛門リフト

アナル（膣ではない）: アナルバック / アナル立ちバック / アナル正常位 / アナル騎乗位 / アナル座位

小便（黄色い水は **亀頭先の尿道口**。マンコ・肛門・画面外から出さない。白・精液・透明禁止）: 放尿（立ち） / 放尿（しゃがみ） / ご褒美小便

脱糞（**肛門から今出す** ソーセージ状の固形。ゼリー／スライム禁止。マンコから出さない。肥溜めの塗れではない）: 脱糞（しゃがみ） / 脱糞（後背）

画風: 入力のまま / アニメ絵 / リアル / 3D / 漫画

入力: Drive input（既定） / アップロード

参照画像: なし（元画像の顔） / Drive から / アップロード。Drive からのときは `参照ファイル名`（input の中）。参照はバッチの元画像から外す。

## 触るファイル（これ以外は触るな）

| 場所 | 役割 |
|---|---|
| `qwen-image-edit-nsfw/HANDOVER.md` | このレーンの引き継ぎ |
| `colab/qwen_image_edit_nsfw.py` | 本体。ロック・プリセット・LoRA 段 |
| `colab/_write_qwen_edit_nb.py` | ノート生成。ipynb は手で直すな |
| `qwen_image_edit_nsfw.ipynb` | root の Colab（バッジ先） |
| `h3-lora-studio/qwen_image_edit_nsfw.ipynb` | 同じものの写し |
| `colab/test_qwen_image_edit_nsfw.py` | 単体テスト |
| `h3-lora-studio/scripts/qwen_edit_nsfw.py` | HF Space 経路。Colab 本体ではない |
| `h3-lora-studio/start-stills.json` | 起点台帳。JPG は Git に無い |

③は GitHub raw から `colab/qwen_image_edit_nsfw.py` を取る。**push しないと Colab は古い。** Drive に保存したコピーは使わない。リンクから開き直す。

## 触るな

- `minimax_h3_lora_studio.ipynb` / `colab/h3_lora_studio.py` / `minimaxh3/h3_lora_studio.py`
- `h3-lora-studio/stories/*.json`（clinic / cafe / sales 含む）
- HQ dump / `hq-instruct.js` / Threads cron
- PR #138 のマージ。新枝

## 起点スチル（Git に無い）

前チャットで Mk1227 編集。Drive `qwen-image-edit-nsfw/input`。H3 に使うなら席1回で `minimax-h3-comfyui/input/phone`。

- 01/02/03/07 服あり → フタナリ全裸勃起（編集済み）
- 04/05/06 元から全裸なので copy
- 08 室内シャツ＋ネクタイの実写 → skip（他人の実写は全裸化するな）

## 使い方

1. 上の Colab リンク（Drive コピーではない）
2. ランタイム → GPU **A100**（40GB でも 80GB でも。H100 可。L4 は offload。T4 は拒否）
3. ① Drive（空きは 2GB で足りる。重みは Colab 約70GB）→ ② 重み（初回は AIO 28GB。Pillow は Colab の `11.3.0` のまま。12 に上げるな。`torchao>=0.16.0`。0.11 は今の git+diffusers で落ちる）→ ③ クイックプロンプト＋画風。**スマホは Drive input**（ファイル選択は使えない）。JPG は Drive `input/`。1枚だけなら 入力ファイル名。キャンバス既定は **auto**。rewrite 既定オン（Secrets に HF_TOKEN）。顔を固定したいときは参照画像（Picture 2）＝Drive から
4. 出力は Drive `qwen-image-edit-nsfw/output`

T4 は拒否される。H3 動画ノートと同時に動かさない。

## 検証

```bash
python3 colab/_write_qwen_edit_nb.py
python3 -m pytest colab/test_qwen_image_edit_nsfw.py -q
```

ipynb を手で直したあとにテストが通っても、次の writer で消える。

## 限界

4step 編集なので、カメラが大きく変わると顔は多少ずれる。ロックは必須だが完全保証ではない。大きく姿勢を変えるときは **参照画像（Picture 2）** に顔のよく出た同じ人物を足す。フタナリ勃起オンなら体（竿・マンコ）は足す。別の人になるときはプロンプトが長すぎるか、②で追加LoRAを載せている。オフのまま開き直して③。

②で `_Ink` や `_imaging was built for another version` は Pillow 12 を Colab の 11.3 拡張の上に載せたせい。リンクから開き直して②を再実行（`pillow==11.3.0`）。まだならランタイム再起動→①②。

②で `cannot import name 'FqnToConfig'` は Space の `torchao==0.11.0` を今の git+diffusers と一緒に入れたせい。ノートを GitHub から開き直して②（`torchao>=0.16.0`。uninstall してから）。まだならランタイム再起動→①②。

②のほか: Qwen VAE に `enable_slicing` が無い（`tune_edit_vae` で hasattr）。`device_map="cuda"` は使わない。A100（35GB以上）は GPU 常駐。L4 は `model_cpu_offload`（sequential は OOM の最後だけ）。Colab の FP8 は `torchao>=0.16.0`（Space の 0.11 は今の git+diffusers で落ちる）。AIO 注入が 0 keys のときだけ prithiv 抽出に落ちる。③はサイズ **auto**（入力のアスペクト。576×1024 も選べる）。`guidance_scale=1.0`。VAE 参照は公式の 1024²。プロンプトは短い編集指示。長い IDENTITY LOCK は顔を捨てる。rewrite は HF_TOKEN が要る（nebius の 72B）。無いときは入力文のまま。③の Generator は A100 なら cuda、offload なら cpu。③は画像を置いてから。**スマホでファイル選択が使えない**のは `files.upload` が iPhone で落ちるせい。入力は Drive input。PCから選ぶはオフのまま。
