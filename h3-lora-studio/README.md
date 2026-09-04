# h3-lora-studio

MiniMax H3 の LoRA を **シチュエーション × モード** で積む。Fal H3 Max には LoRA を差せない。Colab Comfy（T2V / I2V）専用。

成人のみ（21+）。速さ用と画質用を分けて積む。エロ本体は 1 系統だけ。3 本以上の画質 LoRA は穴も竿も顔も崩れる。API キーは print しない。

## Colab（初心者はここだけ）

[minimax_h3_lora_studio.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_lora_studio.ipynb)

1. Open in Colab → GPU を **A100**
2. [Civitai の API Keys](https://civitai.com/user/account) でキーを作り、**②の「CivitaiのAPIキー」欄に貼る**（シネマ質感とえっち用。専用ノートと同じ「普通」だけなら不要）
3. **①** Drive 許可 → **②** 部品ダウンロード（初回は待つ）→ **③** シーンを日本語で選んで実行

Drive `minimax-h3-comfyui` は専用 I2V / T2V ノートと共用。同時に 2 ノートを動かさない。ココナラ homage ノートの Turbo 既定は変えない。

## エロなし（速い＋綺麗）

速さ LoRA と画質 LoRA を分ける。同時オンは **Turbo 1 + 画質 0〜1**。

| 速さ | LoRA | step | メモ |
|---|---|---|---|
| 常用・顔と質感 | larryvrh v4 step600 EMA（Comfy 変換） | 6–8 | 作者推奨。4step は動きが滲む。8超はシャープ過多。強さ 1.0 |
| 最速プレビュー | LightX2V FL2VA 4step 768p v1.0 | 4 | 768p 直出し。音は弱い |
| 音も残して速く | LightX2V FL2VA 8step v1.0 | 8 | 4step より音がマシ。歌・日本語は Larry の方が安定 |
| 顔固定 R2V | LightX2V Ref2VA 4step v0.1 | 4 | FL2VA 用と混ぜない。この Colab では選ばない |

| 画質（エロなし） | 強さ | 効果 |
|---|---|---|
| Authentic cinematic texture（テンソル修正版 2908686、トリガー `DY`） | 0.7（動き多いなら 0.5）。日常は 0.65 | 光・肌・被写界深度。元 2890588 はテンソルエラーがあるので使わない |
| Cinematic Style + Detail（トリガー `ASTROCINEMAV01K2T`） | カタログのみ | DY と同時に積まない。日常は DY を使う |
| Photoreal Image Generator（トリガー `ph0t0r34l`） | — | 静止画・キーフレーム用。動画本体には載せない |

比較の目安: 20step 基準に対し 8step で約半分、4step で約 1/3。8step 同士なら Larry と LightX2V の画質は近い。音は ベース ＞ Larry 8step ＞ LightX2V。

| ③の名前 | situation | Turbo | 画質 | sampler |
|---|---|---|---|---|
| 日常（速い＋綺麗） | `sfw_daily` | Larry 1.0 | シネマ 0.65 | res_multistep / simple / 8 |
| 最速プレビュー（エロなし） | `sfw_preview` | LightX2V 4step 1.0 | シネマ 0.4 | euler / simple / 4 |
| 音も残す（エロなし） | `sfw_audio` | LightX2V 8step 1.0 | シネマ 0.4 | euler / simple / 8 |
| 普通（エロなし） | `vanilla` | LightX2V 4step 1.0 | なし | 専用 I2V / T2V と同じ |
| （R2V・CLI） | `sfw_r2v` | Ref2VA 4step 1.0 | シネマ 0.5 | FL2VA 用 Turbo は積まない |

Larry の公式重みは [larryvrh/MiniMax-H3-Turbo-Lora](https://huggingface.co/larryvrh/MiniMax-H3-Turbo-Lora)。Colab は LoraLoader 用の [DarkRomeo88 Comfy 変換](https://huggingface.co/DarkRomeo88/MiniMax-H3-turbo-lora-comfyui) を使う。LightX2V は [lightx2v/Minimax-h3-Turbo](https://huggingface.co/lightx2v/Minimax-h3-Turbo)。まとめ: [Civitai 1063735](https://civitai.com/models/1063735)。

`video shift 6` / `audio shift 3` は sampler のメモ。グラフに ModelSamplingAV ノードは無いので未配線。SageAttention / Sol-Attn / Spectrum は LoRA ではない（Turbo と併用するとさらに短いが、このノートでは入れない）。

## エロ（既存）

同時オンは **行為 1 + ヘルパー 0〜1 + Turbo 0〜1**。シネマを足すならヘルパーを落とす。挿入 LoRA と SFW の速い＋綺麗は併用しない。CoachBate アナルは Turbo オフ。

| ③の名前 | situation | 行為 | ヘルパー | Turbo | シネマ | sampler |
|---|---|---|---|---|---|---|
| アナル挿入（画質） | `anal_penetration` | CoachBate 0.85 | Synth 0.55 | **切る** | **切る** | res_multistep / beta / 16 |
| アナル舐め・指 | `anal_closeup` | Synth 0.7 | なし | Larry 0.5 | 0.4 | euler / simple / 8 |
| フェラ | `oral` | Blowjob 0.75 | Penis 0.7 | Larry 0.7 | なし | euler / simple / 8 |
| ふたなりフェラ | `futa_blowjob` | Blowjob 0.75 | Penis 0.7 | Larry 0.7 | なし | AIO / Futa LoRA なし |
| 汎用エロ | `general_sex` | AIO 0.75 | なし | LightX2V 0.5 | なし | euler / simple / 12 |
| 試し打ち | `preview` | AIO 0.7 | なし | LightX2V 4step 1.0 | なし | euler / simple / 4 |

## やらないこと

- Turbo を 2 本同時（Larry + LightX2V）
- FL2VA 用と Ref2VA 用の取り違え
- エロ挿入 LoRA との併用（アナル系は Turbo 切るのが前提）
- シネマ DY を 0.7 以上で挿入ショット（SFW 日常は 0.6–0.7）
- Photoreal still を動画本体に載せる
- DY と ASTROCINEMA の同時積み
- Fal H3 Max に LoRA を差す

```bash
python h3-lora-studio/scripts/select_loras.py --list
python h3-lora-studio/scripts/select_loras.py --situation sfw_daily --mode t2v --prompt '（シーン）'
python colab/_write_lora_studio_nb.py
```

T2V は 9:16・first_frame なし。I2V は 8:9・Picture 1 必須。

## 不変条件

1. 速さ用と画質用を分け、Larry と LightX2V を同時に積まない
2. CoachBate アナル挿入は Turbo オフ
3. FL2VA に ref2va を載せない
4. T2V に Picture 1 を書かない
5. 未成年・ロリ・ショタ禁止
6. キーは print しない。Git に入れない
7. ココナラ homage の turbo 既定を変えない
8. Fal に LoRA を載せない
