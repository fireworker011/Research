# h3-lora-studio

MiniMax H3 の LoRA を **シチュエーション × モード** で積む。Fal H3 Max には LoRA を差せない。Colab Comfy（T2V / I2V）専用。

成人のみ（21+）。えっち用は Turbo オフ。普通（エロなし）は専用 I2V / T2V と同じ Turbo。API キーは print しない。

## Colab（初心者はここだけ）

[minimax_h3_lora_studio.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_lora_studio.ipynb)

1. Open in Colab → GPU を **A100**
2. [Civitai の API Keys](https://civitai.com/user/account) でキーを作り、**②の「CivitaiのAPIキー」欄に貼る**（シークレット不要）
3. **①** Drive 許可 → **②** 部品ダウンロード（初回は待つ）→ **③** シーンを日本語で選んで実行

③のリストは日本語（普通／穴アップ／アナル挿入／ふたなりフェラ／フェラ／騎乗位）。**普通（エロなし）** は専用 I2V / T2V と同じ Turbo。えっち用は Turbo オフ。Drive `minimax-h3-comfyui` は共用。同時に2ノートを動かさない。

Civitai API はノートのフォームから読む。値は print しない。ノート保存前に欄を空に戻す。左の鍵（`CIVITAI_API_TOKEN`）でも読めるが、初心者はフォームでよい。

## シチュエーション

| ③の名前 | situation | 積む | 用途 |
|---|---|---|---|
| 普通（エロなし） | `vanilla` | Turbo 4-step のみ | 専用 I2V / T2V と同じ。えっち用なし |
| 穴アップ（舐め・指） | `anal_closeup` | Synth Pussy 0.75 + Anal Penetration 0.85 | 舐め・指・穴アップ。Turbo 切る |
| アナル挿入 | `anal_penetration` | HMNSFW AIO V2.5 + Anal Penetration | セックスで穴が膣に逃げるとき |
| ふたなりフェラ | `futa_blowjob` | Futa v5.1 + Penis 0.7 + Blowjob 0.85 | I2V が安定 |
| フェラ | `oral` | Blowjob + Penis | `bl0w_j0b` / `PENISLORA` |
| 騎乗位 | `riding` | I2V: riding pose / T2V: AIO V2.5 | riding は I2V 専用 |

任意: Astro 0.25–0.5、Tiddies 1.0–2.0、Realism People。Photoreal still は静止画用で穴動画には使わない。gayanalh3 は入れない。

```bash
python h3-lora-studio/scripts/select_loras.py --list
python h3-lora-studio/scripts/select_loras.py --situation anal_closeup --mode t2v --prompt '（シーン）'
```

T2V は 9:16・first_frame なし。I2V は 8:9・Picture 1 必須。sampler は `res_multistep` / `beta` / 16 step。

## 不変条件

1. えっち用に Turbo / Acc を積まない。普通（エロなし）だけ Turbo（専用ノートと同じ）
2. FL2VA に ref2va を載せない
3. T2V に Picture 1 を書かない
4. 未成年・ロリ・ショタ禁止
5. キーは print しない。Git に入れない。Colab は ②のフォーム（またはシークレット）から読む
6. ココナラ homage の turbo 既定を変えない
