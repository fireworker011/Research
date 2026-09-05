---
name: h3-lora-studio
description: MiniMax H3 LoRA studio for Colab. SFW fast+quality is turbo plus one cinematic LoRA (Larry daily, LightX2V preview). Adult stacks stay act + helper-or-cinema + optional thin turbo. Futa blowjob may use two helpers plus thin Larry 6step. CoachBate anal stays turbo off. Use when the user names h3-lora-studio, Colab LoRA, Larry, LightX2V, cinematic DY, or select_loras.py.
---

# h3-lora-studio

質問しない。Colab 実装なら `minimax_h3_lora_studio.ipynb`。設定だけなら `select_loras.py`。ノートは `python colab/_write_lora_studio_nb.py` で再生成。`colab/h3_lora_studio.py` と `minimaxh3/h3_lora_studio.py` は同期する。ココナラ homage ノートの Turbo 既定は変えない。

```bash
python h3-lora-studio/scripts/select_loras.py --list
python h3-lora-studio/scripts/select_loras.py --situation sfw_daily --mode t2v --prompt '（シーン）'
python colab/_write_lora_studio_nb.py
```

Fal に LoRA は差せない。成人 21+。

エロなし: Turbo1 + 画質1。日常は Larry v4 1.0 + シネマ DY 0.65 / 8step。最速は LightX2V 4step。音残しは LightX2V 8step。専用「普通」は LightX2V 4step のみ。Larry と LightX2V は同時に積まない。FL2VA と Ref2VA を混ぜない。Photoreal still は動画本体に載せない。DY と ASTROCINEMA は同時に積まない。

エロ: 行為1 + ヘルパー0〜1 + Turbo0〜1。ふたなりフェラはヘルパー2（竿＋穴）+ Larry 0.5 / 6step。セックス（女体）/ アナルはヘルパー2で Turbo オフ。CoachBate アナルは Turbo オフ・16step。汎用エロ / 騎乗は AIO + Larry 0.5 / 12step（LightX2V にはしない）。セックス（女体）は竿 0.7 + 穴の見え方 0.55。変身 LoRA は足さない。穴の見え方 LoRA は積むが、空欄文は行為本線だけ。マンコ/アナルの強調は③の文章欄。空欄文は挿入・リズム・横クローズを書く。秒数は 1本 4〜15。16〜60秒は最後のコマつなぎ。挿入 LoRA と SFW の速い＋綺麗は併用しない。セックス（女体）/ アナルセックス（女体）は男・筋肉質の男体にしない。
