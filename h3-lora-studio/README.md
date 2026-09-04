# h3-lora-studio

MiniMax H3 の LoRA を **シチュエーション × モード** で積む。Fal H3 Max には LoRA を差せない。Colab Comfy（T2V / I2V）専用。

成人のみ（21+）。エロ本体は 1 系統だけ。速さは薄く。画質 LoRA は弱く。3 本以上重ねると穴も竿も顔も崩れる。API キーは print しない。

## Colab（初心者はここだけ）

[minimax_h3_lora_studio.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_lora_studio.ipynb)

1. Open in Colab → GPU を **A100**
2. [Civitai の API Keys](https://civitai.com/user/account) でキーを作り、**②の「CivitaiのAPIキー」欄に貼る**（シークレット不要）
3. **①** Drive 許可 → **②** 部品ダウンロード（初回は待つ）→ **③** シーンを日本語で選んで実行

Drive `minimax-h3-comfyui` は専用 I2V / T2V ノートと共用。同時に 2 ノートを動かさない。Civitai API はノートのフォームから読む。値は print しない。ノート保存前に欄を空に戻す。

## 重ね上限

同時オンは **行為 1 + ヘルパー 0〜1 + Turbo 0〜1**。シネマを足すならヘルパーを落とす。

| 層 | 本数 | 役割 |
|---|---|---|
| 行為 | 1 | 挿入 / フェラ / 指 / 質感 |
| 部位ヘルパー | 0〜1 | 竿か穴。両方は弱い方を切る |
| Turbo | 0〜1 | 強度は通常より下げる |
| シネマ | 0〜1 | 0.4–0.6。動きが激しいほど下げる。ヘルパーと同時に積まない |

やらないこと:

- Larry と LightX2V の同時積み
- Anal Penetration + AIO + Penis + Synth のフル重ね
- シネマ DY を 0.7 以上で挿入ショット
- Fal に LoRA を載せる
- CoachBate アナル挿入に Turbo（作者注記どおり本命はなし）

最短の常用:

- 本線エロ: CoachBate なし Turbo、または AIO + Turbo 0.5
- 本線フェラ: Penis + Blowjob + Larry 0.7
- 試し打ち: AIO + LightX2V 4step。当たりだけ本線で焼き直し

## シチュエーション

| ③の名前 | situation | 行為 | ヘルパー | Turbo | シネマ | sampler |
|---|---|---|---|---|---|---|
| 普通（エロなし） | `vanilla` | なし | なし | LightX2V 4step 1.0 | なし | euler / simple / 4 |
| アナル挿入（画質） | `anal_penetration` | CoachBate 0.85 | Synth 0.55 | **切る** | **切る** | res_multistep / beta / 16 |
| アナル舐め・指 | `anal_closeup` | Synth 0.7 | なし（ThumbInButt 未入手） | Larry 0.5 | 0.4 | euler / simple / 8 |
| フェラ | `oral` | Blowjob 0.75 | Penis 0.7 | Larry 0.7 | なし | euler / simple / 8 |
| ふたなりフェラ | `futa_blowjob` | Blowjob 0.75 | Penis 0.7 | Larry 0.7 | なし | 同上。AIO / Futa LoRA は足さない |
| 汎用エロ | `general_sex` | AIO 0.75 | なし | LightX2V 0.5 | なし | euler / simple / 12 |
| 試し打ち | `preview` | AIO 0.7 | なし | LightX2V 4step 1.0 | なし | euler / simple / 4 |
| 騎乗位（旧名） | `riding` | AIO 0.75 | なし | LightX2V 0.5 | なし | 汎用エロと同じ薄い積み |

ThumbInButt と FunPhantom DP はカタログに ID がないので入れていない。DP シーンは作らない。上級チェック（リアル寄せ・胸）は重ね上限のため無視する。

```bash
python h3-lora-studio/scripts/select_loras.py --list
python h3-lora-studio/scripts/select_loras.py --situation anal_penetration --mode t2v --prompt '（シーン）'
python colab/_write_lora_studio_nb.py
```

T2V は 9:16・first_frame なし。I2V は 8:9・Picture 1 必須。`普通（エロなし）` の Turbo 既定は専用 I2V / T2V ノートと同じ。

## 不変条件

1. 重ね上限を外さない。Larry と LightX2V を同時に積まない
2. CoachBate アナル挿入は Turbo オフ。どうしても速くするなら Larry 0.4–0.5 / 8step（1.0 は穴が膣に逃げる）
3. FL2VA に ref2va を載せない
4. T2V に Picture 1 を書かない
5. 未成年・ロリ・ショタ禁止
6. キーは print しない。Git に入れない。Colab は ②のフォーム（またはシークレット）から読む
7. ココナラ homage の turbo 既定を変えない
8. Fal に LoRA を載せない
