---
name: h3-lora-studio
description: MiniMax H3 LoRA studio for Colab. Thin NSFW stacks by situation (anal_penetration, anal_closeup, oral, futa_blowjob, general_sex, preview). Cap is act + helper-or-cinema + optional thin turbo. CoachBate anal stays turbo off. Use when the user names h3-lora-studio, Colab LoRA, CoachBate, Synth Pussy, Larry, LightX2V, or select_loras.py.
---

# h3-lora-studio

質問しない。Colab 実装なら `minimax_h3_lora_studio.ipynb`（初心者向け・日本語フォーム）。設定だけなら `select_loras.py`。ノートは `python colab/_write_lora_studio_nb.py` で再生成。英語 id は内部用。画面の選択肢は日本語。`colab/h3_lora_studio.py` と `minimaxh3/h3_lora_studio.py` は同期する。

```bash
python h3-lora-studio/scripts/select_loras.py --list
python h3-lora-studio/scripts/select_loras.py --situation anal_penetration --mode t2v --prompt '（シーン）'
python colab/_write_lora_studio_nb.py
```

Fal H3 Max に LoRA は差せない。成人 21+。重ね上限は 行為1 + ヘルパー0〜1 + Turbo0〜1。シネマを足すならヘルパーを落とす。Larry と LightX2V は同時に積まない。CoachBate アナル挿入は Turbo オフ。`普通（エロなし）` は専用 I2V/T2V と同じ LightX2V 4step。Drive `minimax-h3-comfyui` 共用。ココナラ homage ノートの既定は変えない。Civitai API は Colab ②のフォームから読む。値は print しない。gayanalh3 は使わない。

最短の常用: 本線エロは CoachBate なし Turbo か AIO+LightX2V 0.5。本線フェラは Penis+Blowjob+Larry 0.7。試し打ちは AIO+LightX2V 4step。
