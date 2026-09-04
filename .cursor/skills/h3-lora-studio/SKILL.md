---
name: h3-lora-studio
description: MiniMax H3 LoRA stack from a studio profile. Run scripts/select_loras.py, load enabled only, unload disabled, Turbo off, adults only. Do not print API keys. Use when the user names h3-lora-studio, a LoRA profile (anal_penetration), or select_loras.py.
---

# h3-lora-studio

質問しない。次を実行して JSON を出す。

```bash
python h3-lora-studio/scripts/select_loras.py --profile anal_penetration --mode i2v --prompt '（シーン）'
```

profile / mode はユーザー指定を使う。`prompt: （シーン）` は profile の `scene`。

## ルール

- **enabled だけ** `LoraLoaderModelOnly` を直列で積む
- **disabled はアンロード**（Turbo 含む。I2V に ref2va を載せない）
- **Turbo オフ** → `res_multistep` / `beta` / steps ≥ 16。4-step euler にしない
- **成人のみ**（21+）。shota / loli / Live2D syota 禁止
- **API キーは `.env` 以外に出さない**。スクリプトは `.env` を読まない
- ココナラ homage ジョブや Threads schedule を触らない
- I2V は first_frame 必須。このスクリプトは LoRA 設定だけ出す

空のときは設定 JSON だけ書いて終わる。投稿しない。
