# h3-lora-studio

MiniMax H3 の LoRA を **シチュエーション × モード** で積む。Fal H3 Max には LoRA を差せない。Colab Comfy（T2V / I2V）専用。

成人のみ（21+）。Turbo オフ。API キーは `.env` / Colab シークレットだけ。

## Colab

[minimax_h3_lora_studio.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_lora_studio.ipynb)

セル① Drive → ② 本体+LoRA（Turbo は入れない）→ ③ SITUATION で組み合わせ。推奨プロンプトはノート先頭。

Civitai 用: Colab シークレット `CIVITAI_API_TOKEN`。ログに出さない。

## シチュエーション

| situation | 積む | 用途 |
|---|---|---|
| `anal_closeup` | Synth Pussy 0.75 + Anal Penetration 0.85 | 舐め・指・穴アップ。Turbo 切る |
| `anal_penetration` | HMNSFW AIO V2.5 + Anal Penetration | セックスで穴が膣に逃げるとき |
| `futa_blowjob` | Futa v5.1 + Penis 0.7 + Blowjob 0.85 | I2V が安定 |
| `oral` | Blowjob + Penis | `bl0w_j0b` / `PENISLORA` |
| `riding` | I2V: riding pose / T2V: AIO V2.5 | riding は I2V 専用 |

任意: Astro 0.25–0.5、Tiddies 1.0–2.0、Realism People。Photoreal still は静止画用で穴動画には使わない。gayanalh3 は入れない。

```bash
python h3-lora-studio/scripts/select_loras.py --list
python h3-lora-studio/scripts/select_loras.py --situation anal_closeup --mode t2v --prompt '（シーン）'
```

T2V は 9:16・first_frame なし。I2V は 8:9・Picture 1 必須。sampler は `res_multistep` / `beta` / 16 step。

## 不変条件

1. Turbo / Acc を積まない
2. FL2VA に ref2va を載せない
3. T2V に Picture 1 を書かない
4. 未成年・ロリ・ショタ禁止
5. キーは `.env` / Colab Secrets 以外に出さない
6. ココナラ homage の turbo 既定を変えない
