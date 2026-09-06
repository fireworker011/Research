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

エロ: 行為1 + ヘルパー0〜2 + Turbo0〜1。空欄は全裸のごく普通の若い成人女性（21+）。女かふたなりのみ。男厳禁。描写は③の文章欄。ふたなりフェラはヘルパー2（竿＋穴）+ Larry 0.5 / 6step。セックス（女体）/ アナル / 騎乗 / 後背位はヘルパー2で Turbo オフ。CoachBate アナルは Turbo オフ・16step。体位 LoRA は AIO の代わり（同時に積まない）。騎乗は cowgirl + 竿 + 穴 / 12step。後背位は doggy + 竿 + 穴 / 12step。正常位POVは POV + 竿 + Larry 0.5 / 8step（横はセックス（女体））。後射精は HMCumshot + 竿 + Larry 0.5 / 8step。顔射は cmst + 竿 + Larry 0.5 / 8step（後射精・絶頂とは別。I2V本線）。指入れは膣。アナル指入れは ThumbInButt + 穴 + Larry 0.5 / 8step（I2V本線。指入れ・CoachBate・AIO・竿とは積まない）。指入れとオナニーは別シーン（同時に積まない）。足コキは Type D + 竿 + Larry。絶頂は Remoteorgasm（射精ではない）。汎用エロ（女体）は AIO + Larry 0.5 / 12step。変身 LoRA は足さない。riding-pose-i2v は I2V専用で未使用。秒数は 1本 4〜15。20〜90秒は最後のコマつなぎ（③の「つなぐ 20秒」〜「つなぐ 90秒」。秒数欄は無視）。90秒は 10×9。任意の 16〜90 は「つなぐ（秒数欄・16〜90）」。2〜9本目は③のつなぎ欄（空なら前の続き）。挿入 LoRA と SFW の速い＋綺麗は併用しない。訓練で体位を足さない。
