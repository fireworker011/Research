---
name: h3-lora-studio
description: MiniMax H3 LoRA studio for Colab. Stack Civitai NSFW LoRAs by situation (anal_closeup, anal_penetration, futa_blowjob, oral, riding), T2V or I2V, turbo off, adults only. Use when the user names h3-lora-studio, Colab LoRA, CoachBate anal, Synth Pussy, or select_loras.py.
---

# h3-lora-studio

質問しない。Colab 実装なら `minimax_h3_lora_studio.ipynb`（初心者向け・日本語フォーム）。設定だけなら `select_loras.py`。ノートは `python colab/_write_lora_studio_nb.py` で再生成。英語 id（`anal_closeup` 等）は内部用。画面の選択肢は日本語。

```bash
python h3-lora-studio/scripts/select_loras.py --list
python h3-lora-studio/scripts/select_loras.py --situation anal_closeup --mode t2v --prompt '（シーン）'
python colab/_write_lora_studio_nb.py
```

Fal H3 Max に LoRA は差せない。成人 21+。えっち用は Turbo オフ。`普通（エロなし）` は専用 I2V/T2V と同じ Turbo。Drive `minimax-h3-comfyui` 共用。ココナラ homage ノートの既定は変えない。Civitai API は Colab ②のフォームから読む。値は print しない。gayanalh3 は使わない。
