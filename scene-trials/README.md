# scene-trials

Project-switchable scene trial runner. It plans N trials per scene, files the
results as `{project}/{section}/{scene_id}/trial_N/`, builds contact sheets,
records which trial wins, and writes cutout commands for the winners.

Image generation is a pluggable backend and is optional. This release has the
`import_only` backend (files that already exist). The `sd_diff_set` backend
and a plain `webui_api` backend come next.

This package is independent of the sd-diff-set factory and of everything else
in this repository.

## Quick start

```sh
cd scene-trials
pip install -e .            # PyYAML and Pillow
cp -r projects/_template projects/myproject   # then edit project.yaml
scene-trials lint   --project projects/myproject
scene-trials plan   --project projects/myproject
scene-trials collect --project projects/myproject --source /path/to/finished/images
scene-trials sheet  --project projects/myproject
scene-trials pick   --project projects/myproject S03_holding_01 2
scene-trials finalize    --project projects/myproject
scene-trials cutout-cmds --project projects/myproject   # writes .ps1 and .sh, runs nothing
python -m unittest discover -s tests
```

## One project = one folder

| File | Holds |
| --- | --- |
| `project.yaml` | output root, trial count and order, batch cap, canvas size, prompt rules, safety declaration, cutout templates, backend |
| `scenes.csv` | one row per deliverable. Column names are set in `project.yaml` |
| `chains.yaml` | optional: scenes that share one base image and dependent stages |
| `loras.yaml` | optional: trigger word to `<lora:file:weight>` |
| `negatives.yaml` | optional: negatives added to every scene, or per section |

`SCENE_TRIALS_OUT_ROOT` overrides `paths.out_root` for one machine. A Windows
drive path on another OS is refused until that variable is set. Output roots
containing `Picture/CG` or `.library` are refused.

## Concepts

* **scene**: one CSV row. Its id is `S{row}` plus the `id_columns` values.
* **chain**: one base image and ordered stages. Each scene in a chain names the
  stage it wants. A job asks the backend for the stages up to the last one any
  scene needs, because a later stage cannot run without the earlier ones.
* **solo scene**: a scene in no chain. It needs only a base image.
* **job**: one base image for one trial. A chain job serves several scenes.

## Folder layout

```
{out_root}/{project}/
  {section}/{scene_id}/trial_N/   result.png, result.transparent.png, base.png, masks/, manifest.json
  {section}/{scene_id}/selected/  the picked image, its transparent copy, selected.json
  _chains/{chain}/trial_N/        every file of the chain, plus job.json
  _meta/                          scene_index.csv, jobs.json, batches/, sheets/, selection.csv,
                                  collect-report.json, cutout_commands.ps1|sh
```

Files are copied, never moved. A destination that already holds different
bytes is reported as a conflict and kept unless `--overwrite` is given.

## import_only naming

`{scene_id}__t{N}.png` is the base, `{scene_id}__t{N}__{stage}.png` is a stage,
`.transparent` or `.mask` goes before the extension. Or give an index CSV with
`path,scene_id,trial,role,stage` and optional `ok,error_code`.

## Safety (not switchable from a project file)

* The negative prompt always carries `child, loli, teen`.
* A positive prompt with a blocked word (whole-word match, so `lolita` counts and
  `glorious` does not) stops that scene's plan with `cast_excluded`.
* `export` needs `safety.adult_confirmed_by` and `adult_confirmed_on`. A person
  fills them. The tool does not judge any picture's age.
* `cutout-cmds` writes commands and does not run them.

## Lint warnings you may see

* `composition_conflict`: a `landscape composition` tag on a portrait canvas.
  Set `prompt.composition: drop` to remove such tags, or fix the CSV.
* `face_hint_missing`: a chain marked `needs_face_visible`, resolved to
  `face_pass: required`, whose base prompt has none of `face_visible_hints`. A
  stage that detects the face may stop the chain.

## Face pass

Some backends repaint the face in a stage and fail the stage when no face is
found. Each chain job carries `face_pass`:

* `required`: stop when the face is not found (the factory's current behavior).
* `skip`: do not repaint the face.
* `optional`: try, and continue without the face repaint when none is found.
* `auto` (project default): `skip` when the base prompt names a word from
  `rear_view_hints` and none from `face_visible_hints`; otherwise `required`.
  `looking back` therefore wins over `from behind`.

`chains.yaml` can set `face_pass` per chain. The value is written to `jobs.json`,
the batch files and each `manifest.json`. A backend that cannot honor `skip` or
`optional` must refuse the job rather than ignore the field.

## Private project data

`projects/pronant/` holds configuration only. Its `scenes.csv` is git-ignored
because this repository is public. Copy the CSV in locally.
