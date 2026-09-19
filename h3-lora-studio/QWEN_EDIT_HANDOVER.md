# Qwen Image Edit NSFW 引き継ぎ（画像編集 Colab のみ）

H3 動画スタジオは別。このファイルは **静止画編集ノート** だけ。

## 新規チャットに貼る文

```
Qwen Image Edit NSFW（画像編集 Colab）を続ける。H3 動画は別チャットで引き継ぎ済み。触るな。Naomiichi。

まず読め:
- `h3-lora-studio/QWEN_EDIT_HANDOVER.md`
- `colab/qwen_image_edit_nsfw.py`
- `colab/_write_qwen_edit_nb.py`

作業ブランチ: `cursor/h3-anal-stories-f112` だけ。新枝禁止。PR #138 は draft のままマージするな。
HEAD: e48b78a h3: Qwen Edit に放尿・ご褒美小便・脱糞。顔と画風は必須固定
Colab: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-anal-stories-f112/qwen_image_edit_nsfw.ipynb

目的: 元画像の顔と画風は変えない。変えてよいのは服・姿勢・場所・行為。
基本フタナリ（玉なし・マンコあり・竿20cm）。男禁止。成人21+。実写の他人は入れるな。JPGはGitに入れるな。
ipynb は手で直すな。`python3 colab/_write_qwen_edit_nb.py`。H3 スタジオと同時に動かすな。
JSON物語（clinic/cafe/sales含む）は触るな。HQ dump / hq-instruct / Threads cron は触るな。
```

## リンク

- Colab: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-anal-stories-f112/qwen_image_edit_nsfw.ipynb
- 枝: `cursor/h3-anal-stories-f112`
- PR: https://github.com/fireworker011/Research/pull/138 draft vs `cursor/h3-cabin-flow-f112`。マージ禁止
- 版は動画側の `h3-20260914-anal-18` のまま（このノートは版を増やしていない）

## 何をするノートか

起点の静止画を **Qwen Image Edit** で直す。H3 動画ノート（`minimax_h3_lora_studio.ipynb`）とは別ランタイム。

Mk1227 / ayooo123 Space と同系統:

- 土台 `Qwen/Qwen-Image-Edit-2511`
- NSFW マージ `prithivMLmods/Qwen-Image-Edit-Rapid-AIO-V23`
- 4step / CFG1 / guidance 1.0 / 576×1024
- `safety_checker` なし
- GPU は **L4**（T4 は②で落とす。VRAM 20GiB 未満は拒否）

保存先は Drive `qwen-image-edit-nsfw/output`。Git に JPG を入れない。

HF ZeroGPU 経由の別経路は `h3-lora-studio/scripts/qwen_edit_nsfw.py`（本命 Mk1227 `/infer`）。Colab GPU 経路と混ぜない。

## 必須ロック

毎回のプロンプトに入る。外すな。

| 固定 | 内容 |
|---|---|
| 顔 | `IDENTITY_LOCK`。同一人物・同一顔・髪。美化禁止 |
| 画風 | `STYLE_PRESETS`。変換しない。既定 **入力のまま**。欄の アニメ絵／リアル／3D／漫画 は「元がどれか」の固定 |
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

## 触るファイル（これ以外は触るな）

| 場所 | 役割 |
|---|---|
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

前チャットで Mk1227 編集。Drive `input/phone` 用。

- 01/02/03/07 服あり → フタナリ全裸勃起（編集済み）
- 04/05/06 元から全裸なので copy
- 08 室内シャツ＋ネクタイの実写 → skip（他人の実写は全裸化するな）

## 使い方

1. 上の Colab リンク（Drive コピーではない）
2. ランタイム → GPU **L4**
3. ① Drive → ② 重み（初回は待つ）→ ③ クイックプロンプト＋画風＋画像
4. 出力は Drive `qwen-image-edit-nsfw/output`

T4 は拒否される。H3 動画ノートと同時に動かさない。

## 検証

```bash
python3 colab/_write_qwen_edit_nb.py
python3 -m pytest colab/test_qwen_image_edit_nsfw.py -q
```

ipynb を手で直したあとにテストが通っても、次の writer で消える。

## 限界

4step 編集なので、カメラが大きく変わると顔は多少ずれる。ロックは必須だが完全保証ではない。フタナリ勃起オンなら体（竿・マンコ）は足す。
