---
name: h3-prompt-writing
description: Write MiniMax H3 video generation prompts for T2VA, I2VA, FL2VA, L2VA, and Ref2VA. Use when rewriting multimodal requests into H3 prompt structures, composing integrated_multimodal_description, overall_soundscape, and non_diegetic_music, aligning keyframes, or defining reference labels for images, videos, and audio. Do not use this to rewrite minimaxh3/episodes episode.json action lines; those follow each episode HANDOFF.
compatibility: Portable to any agent that can read local files — no external API calls, MiniMax Hub tools, or proprietary runtime required. The agents/openai.yaml file only adds optional ChatGPT/Codex UI metadata; it does not restrict the skill to OpenAI agents.
---

# H3 Prompt Writing

## Workflow

1. Identify the input mode: T2VA, I2VA, FL2VA, L2VA, or full-reference Ref2VA.
2. For base text/keyframe modes, read `references/base-en.txt` and follow its final prompt structure.
3. For full-reference mode, read `references/ref-en.txt` and follow its six-section rewrite format.
4. Preserve the exact field names, section order, labels, and timing notation from the selected guide.

## Base Modes

- T2VA: build the full audiovisual timeline from text.
- I2VA: start from the first frame and develop forward from it.
- FL2VA: describe the continuous path between the first and last frames.
- L2VA: infer a plausible opening and converge to the supplied last frame.

Use `integrated_multimodal_description`, `overall_soundscape`, and `non_diegetic_music` in the order shown in `references/base-en.txt`.

## Full-Reference Mode

Ref2VA rewrites use `subject_definitions`, `summary`, `retention_analysis`, `detailed_description`, `overall_soundscape`, and `non_diegetic_music` in that order. Reference labels stay consistent across all sections.

Read `references/ref-en.txt` for label rules, retention analysis, and complete examples.

## Output Rules

- Write rewrite sections in English; preserve dialogue, lyrics, and visible scene text in their original language.
- Describe each shot by composition, subjects, environment, actions, camera, sound, and the exact point where referenced content appears.
- Avoid plot summaries, unresolved reference labels, and timing that does not match the requested duration.
## Tips for Better Results
- Always match the total duration of the description to the requested video length (4–15 seconds).
- Keep reference labels consistent (e.g. `<Picture 1>`, `<Video 1>`, `<Audio 1>`) across every section.
- Prefer concrete visual and audio details over abstract words like "cinematic" or "beautiful".
- When using keyframes (I2VA / FL2VA / L2VA), clearly state how the first and/or last frame connects to the timeline.

## このリポジトリ

出典は [MiniMax-AI/MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3) の `skills/h3-prompt-writing`（`d21241f0a4b3acbb34c97dae47fa417b7065e438`）。`references/base-en.txt` と `references/ref-en.txt` はそのまま。

このガイドは H3-Base / API の T2VA、I2VA、FL2VA、L2VA、Ref2VA 用。`minimaxh3/episodes/` の `episode.json` の action は各話の HANDOFF と既存の episode スキルが正。そこの action を `integrated_multimodal_description` に書き替えない。

同じリポジトリの残り 8 スキル（広告、3D、紙工作など）は MiniMax Hub の canvas 用で、ここには置いていない。

36.053秒の縦動画（https://x.com/third0804064/status/2108983936353485033）は、動作の経路の参考だけに使う。台本にはしない。mp4 は置かない。画面の字は写さない。絵とカメラに元の名は書かない。速度は測っていない。ショットの内側の秒は書かない。

scdet=10 のカットは 1.800、6.967、11.800、13.167、16.300、18.167、20.467、22.667、27.533 秒。室内から屋外の背中へ戻るあいだに、絵が重なるコマがある。この閾値が出した境は 27.533 秒だけなので、別のカット秒は足さない。

シートの絵が次の文を持つとき、`picture_prompt` はその名称ではなく経路を書く。今の 71.552秒、真夏の庭、ふみふみ検品には、この文は無い。

- 背中を向けて座り、頭を向かい合わせる
- 口に細い棒をくわえる（顎は動かない。言葉の形は作らない）
- 前足を一本口の棒へ上げて下ろす（棒は口を離れる）
- 前足を一本、胸の前で上げたまま
- 後ろ脚で立ち、前足二本で縦の棒を胸の前で握る
- 前足二本で縦の棒を頭の横へ上げる
- 前足で縦の棒を頭の上に横たえる
- 片手を頭の上へ上げる
- まぶたをきつく閉じ、歯が見える（顎は言葉の形を作らない）
- 両膝を床につけ、両手を床の平たい物に置く
- 床を離れて前へ飛ぶ
- 縦の棒が床へ落ちる
- 後ろの体はぼける
