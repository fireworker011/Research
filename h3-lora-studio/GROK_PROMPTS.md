# Grok 用：このエロ動画レーンの GitHub プロンプト

独立 H3 レーン。Naomiichi。質問しない。
版 `h3-20260913-anal-9`。枝 `cursor/h3-anal-stories-f112`。

**全文はこれを開け:** [`h3-lora-studio/dump/G_h3_prompts.txt`](dump/G_h3_prompts.txt)

HQ dump（`G_hq_boot` / `hq-instruct` / `G_hq_admin`）は触るな。Threads の schedule を戻すな。

再生成:

```bash
python h3-lora-studio/scripts/dump_grok_prompts.py --write
python h3-lora-studio/scripts/dump_grok_prompts.py --check
```

## 何が載るか

Colab ③が H3 に渡す文の **GitHub 上の出所**。実行時に `prepare_story_clip` がロックを足す。
ロック定数も GitHub（`colab/h3_lora_studio.py`）にあるので全文ダンプに入れる。

| 出所 | 役割 | GitHub |
|---|---|---|
| `prompts/h3-body-lock.md` | アナル穴ロック（人間向け。英語は py と同期） | [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/prompts/h3-body-lock.md) |
| `h3-lora-studio/stories/*.json` | 物語クリップの `prompt`（41 話） | [stories](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories) |
| `h3-lora-studio/profiles/*.json` | ③の行為シーン既定 `scenes.t2v` / `scenes.i2v`（33） | [profiles](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles) |
| `colab/h3_lora_studio.py` | 注入ロック・`SITUATION_HELP`・③アナル三択・短編集 | [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/colab/h3_lora_studio.py) |
| `minimaxh3/h3_lora_studio.py` | 上の写し | [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/minimaxh3/h3_lora_studio.py) |

## 物語 JSON（クリップ本文）

- `homecoming-90s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/homecoming-90s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/homecoming-90s.json)
- `dishes-90s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/dishes-90s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/dishes-90s.json)
- `commute-120s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/commute-120s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/commute-120s.json)
- `lecture-120s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/lecture-120s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/lecture-120s.json)
- `rooftop-100s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/rooftop-100s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/rooftop-100s.json)
- `okaeri-120s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/okaeri-120s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/okaeri-120s.json)
- `bath-120s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/bath-120s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/bath-120s.json)
- `dinner-120s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/dinner-120s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/dinner-120s.json)
- `futon-120s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/futon-120s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/futon-120s.json)
- `sunday-120s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/sunday-120s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/sunday-120s.json)
- `engawa-120s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/engawa-120s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/engawa-120s.json)
- `sales-visit-60s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/sales-visit-60s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/sales-visit-60s.json)
- `checkup-100s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/checkup-100s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/checkup-100s.json)
- `clinic-75s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/clinic-75s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/clinic-75s.json)
- `last-stop-40s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/last-stop-40s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/last-stop-40s.json)
- `last-train-120s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/last-train-120s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/last-train-120s.json)
- `semen-bath-70s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/semen-bath-70s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/semen-bath-70s.json)
- `meat-wall-85s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/meat-wall-85s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/meat-wall-85s.json)
- `meat-wall-cesspit-70s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/meat-wall-cesspit-70s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/meat-wall-cesspit-70s.json)
- `cafe-100s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/cafe-100s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/cafe-100s.json)
- `train-sales-80s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/train-sales-80s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/train-sales-80s.json)
- `red-light-50s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/red-light-50s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/red-light-50s.json)
- `yoga-50s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/yoga-50s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/yoga-50s.json)
- `back-wash-60s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/back-wash-60s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/back-wash-60s.json)
- `karaoke-50s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/karaoke-50s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/karaoke-50s.json)
- `laundromat-50s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/laundromat-50s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/laundromat-50s.json)
- `lecture-desk-50s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/lecture-desk-50s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/lecture-desk-50s.json)
- `camp-50s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/camp-50s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/camp-50s.json)
- `fireworks-50s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/fireworks-50s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/fireworks-50s.json)
- `cabin-40s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/cabin-40s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/cabin-40s.json)
- `manhole-30s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/manhole-30s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/manhole-30s.json)
- `roof-ac-30s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/roof-ac-30s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/roof-ac-30s.json)
- `tetrapod-30s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/tetrapod-30s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/tetrapod-30s.json)
- `locker-30s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/locker-30s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/locker-30s.json)
- `crossing-30s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/crossing-30s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/crossing-30s.json)
- `lookout-30s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/lookout-30s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/lookout-30s.json)
- `factory-30s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/factory-30s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/factory-30s.json)
- `gas-station-30s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/gas-station-30s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/gas-station-30s.json)
- `tunnel-phone-30s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/tunnel-phone-30s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/tunnel-phone-30s.json)
- `riverbank-30s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/riverbank-30s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/riverbank-30s.json)
- `hachiko-30s` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/hachiko-30s.json) · [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-anal-stories-f112/h3-lora-studio/stories/hachiko-30s.json)

## ③がコードで組む文（JSON ではない）

- `anal-p1-oral` / `anal-p2-bj-anal` / `anal-p3-meet-anal` → `generate_anal_pattern()`
- `shorts-immoral` → `generate_immoral_shorts()`

全文はダンプの GENERATED 節。

## 使わない（このエロ動画の本線ではない）

- `minimaxh3/coconala_h3_i2va_prompt.txt`
- `colab/h3_t2v.py DEFAULT_T2V_PROMPT (ココナラ homage / 空欄のエロなし既定)`

## 開けるな（本線 HQ）

- `dump/G_hq_boot.txt`
- `dump/G_hq_admin.txt`
- `dump/G_hq_human_sitting.txt`
- `affiliate-engine/docs/grok-bots/hq-instruct.js`

## シーン既定（profiles）

- `after_ejaculation` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/after_ejaculation.json)
- `anal_closeup` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/anal_closeup.json)
- `anal_fingering` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/anal_fingering.json)
- `anal_penetration` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/anal_penetration.json)
- `creampie` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/creampie.json)
- `cunnilingus_futa` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/cunnilingus_futa.json)
- `doggy` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/doggy.json)
- `facial` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/facial.json)
- `fingering` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/fingering.json)
- `footjob` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/footjob.json)
- `futa_anal` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/futa_anal.json)
- `futa_blowjob` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/futa_blowjob.json)
- `futa_masturbation` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/futa_masturbation.json)
- `futa_sex` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/futa_sex.json)
- `futa_visible` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/futa_visible.json)
- `general_sex` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/general_sex.json)
- `lesbian_cunnilingus` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/lesbian_cunnilingus.json)
- `lesbian_spread` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/lesbian_spread.json)
- `masturbation` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/masturbation.json)
- `missionary_pov` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/missionary_pov.json)
- `oral` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/oral.json)
- `oral_creampie` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/oral_creampie.json)
- `preview` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/preview.json)
- `pussy_spread` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/pussy_spread.json)
- `remote_orgasm` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/remote_orgasm.json)
- `riding` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/riding.json)
- `scat_act` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/scat_act.json)
- `sfw_audio` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/sfw_audio.json)
- `sfw_daily` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/sfw_daily.json)
- `sfw_preview` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/sfw_preview.json)
- `sfw_r2v` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/sfw_r2v.json)
- `urine_drink` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/urine_drink.json)
- `urine_pee` — [blob](https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/profiles/urine_pee.json)
