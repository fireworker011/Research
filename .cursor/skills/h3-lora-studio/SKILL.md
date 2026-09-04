---
name: h3-lora-studio
description: MiniMax H3 LoRA stack from a situation profile. Run scripts/select_loras.py for t2v or i2v, load enabled only, unload disabled, Turbo off, adults only. Do not print API keys. Use when the user names h3-lora-studio, a LoRA situation (anal_penetration, oral, riding), T2V LoRA, or select_loras.py.
---

# h3-lora-studio

質問しない。mode はユーザー指定。無指定なら i2v だった会話を引き継がず、書いてある mode を使う。

シチュエーション一覧:

```bash
python h3-lora-studio/scripts/select_loras.py --list
```

T2V（first_frame なし・9:16）:

```bash
python h3-lora-studio/scripts/select_loras.py --situation anal_penetration --mode t2v --prompt '（シーン）'
```

I2V（Picture 1 必須・8:9）:

```bash
python h3-lora-studio/scripts/select_loras.py --profile anal_penetration --mode i2v --prompt '（シーン）'
```

`prompt: （シーン）` は `scenes.<mode>`。T2V に I2V 文面を使わない。

## ルール

- シチュエーションごとに **enabled だけ** `LoraLoaderModelOnly` を直列で積む
- 他シチュエーションと Turbo は **アンロード**。FL2VA（t2v/i2v）に ref2va を載せない
- **Turbo オフ** → `res_multistep` / `beta` / steps ≥ 16
- **成人のみ**（21+）。shota / loli / Live2D syota 禁止
- **API キーは `.env` 以外に出さない**。スクリプトは `.env` を読まない
- ココナラ homage ジョブや Threads schedule を触らない
- T2V は静止画なし。I2V は first_frame 必須。このスクリプトは LoRA 設定だけ出す

空のときは設定 JSON だけ書いて終わる。投稿しない。
