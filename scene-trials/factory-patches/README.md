# factory patches

Proposals against the sd-diff-set extension (`C:\work\sd-diff-set\extensions\sd-diff-set`, shared as
`sd-diff-set.zip`; its 26 files of the 11/13 remodel match `MANIFEST.md`
`69be2044f3e64aae064add2c38a21dd9fd3fda4f2b58390f4bb1e096cc415b19`). Nothing here has been applied to
the factory.

## 0001-face-pass-mode.patch

Adds an opt-in `face_pass` to the factory and a `none` stage filter. Defaults keep today's behavior.

| `face_pass` | behavior |
| --- | --- |
| `required` (default) | unchanged: a stage that repaints the face stops with `mask_empty` when no face is found |
| `skip` | the planner drops the face repaint for every stage that has one; each such item gets the warning `face_pass_skipped` |
| `optional` | the face repaint is tried; only `mask_empty` from the face detector is forgiven. The stage continues without it and gets the warning `face_pass_skipped`. Any other error (for example `mask_model_missing`) still stops the stage |

`stages: ["none"]` is an explicit "no pattern stages" (hands, feet and add-ons are unaffected). Before,
an unknown stage name had the same effect but printed a `stage_filter` warning.

Where the value can be set, from the most specific:

* a factory job: `"face_pass": "skip"` next to `"stages"` (checked before anything is posted; a bad value
  is `bad_face_pass`),
* `pipeline.face_pass` in `config.json`,
* `--face-pass` on `plan`, `patterns`, `route`, `watch` and `factory`.

It reaches `Pipeline._paint` through the ledger row, then `route_file`, `run_job` and `build_plan`. The
manifest item gains `face_optional`.

## How to apply

Use `apply_patches.py`. It reads the two patch files and applies them by content: it ignores line numbers and
line endings, keeps each file's own line ending, skips a hunk that is already there, and writes nothing unless
every file matched.

```
python apply_patches.py <path to extensions/sd-diff-set> --check     # report only
python apply_patches.py <path to extensions/sd-diff-set>             # apply 0001 through 0005
python rebuild_bundle.py <path to extensions/sd-diff-set> --zip factory_extension.zip
```

Why `git apply` failed on `C:\work\sd-diff-set`: the patches have LF line endings. A Windows checkout with
`core.autocrlf` turns the files into CRLF, so every context line differs. This was reproduced here by converting
the shared tree to CRLF: `git apply --check` fails in `cli.py`, `executor.py` and the others, while
`apply_patches.py` applies cleanly and leaves every file CRLF.

`apply_patches.py` was tried on the shared tree as it is, converted to CRLF, and with unrelated lines added at the
top and bottom of every patched file (so every line number moves). It was run repeatedly on each (a record in
`.sd-diff-set-patches.json` skips a patch it already applied; `--force` ignores the record and relies on per-hunk
detection), and on 16 random half-patched states of the kind `git apply --reject` leaves behind (some hunks already
in, half of them CRLF). Every case ends with the same files as the verified tree and all 194 factory tests passing.
If a hunk really does not match, it names the file, the hunk, and the
first line it looked for, and writes nothing. Send that file and I can regenerate the patch against your copy.

### What is verified

* The patch applies to the shared tree (`git apply` on LF, `apply_patches.py` on LF and CRLF) and the factory's
  156 existing tests still pass.
* It adds `tests/test_face_pass.py` with 16 tests. On the unpatched tree 14 of those 16 fail, so they do
  exercise the change.
* `integration/check_sd_diff_set.py` and `integration/run_project.py` run the real factory with only the GPU
  parts replaced, against the patched and the unpatched tree.
* Weights: the factory's tests need the four detector files to exist. They do not read them. Point
  `SD_DIFF_WEIGHTS_DIR` at a folder of empty files when running on a machine without the real weights.

## 0002-limb-repairs-feed-the-diffs.patch (apply after 0001)

Fixes a bug that was already in the factory. `Pipeline._produced_image` read `item["output_path"]`, but the
manifest item key is `"path"`, so the hands and feet repairs never reached the diffs: each ran on the original
sorted base, the ledger's `working` stayed equal to `sorted`, and every diff started from the unrepaired base.

The one-word fix alone is not safe. Tried on the real code it would have:

* renamed every diff folder after the repaired file (`{id}_001_diff-hands-fingers_001_diff-feet-toes/`),
* added the hand and foot tags and negatives to every stage prompt, because the repaired file carries the
  limb prompt in its parameters,
* let the feet repair's leftover `{name}.mask.png` pass for a hand-drawn mask, because the anal, vaginal,
  fellatio and scat presets look for exactly that name next to their base. A stage that finds it only paints
  where that mask overlaps the detected organ, so it would stop with `mask_empty` or `mask_too_wide`. A hand mask
  the user placed next to the sorted base would no longer be found either.

So 0002 reads both keys and, when a repair succeeded, copies the final repaired file to
`diffs/limbs/{category}/work/{base name}.png` with the base's own parameters and the base's hand-drawn
masks, and starts the diffs from that copy. What changes for you:

| | before | after 0002 |
| --- | --- | --- |
| pixels the diffs start from | the original base | the hands-and-feet repaired base |
| diff folder and file names | `diffs/{cat}/{id}/...` | unchanged |
| stage prompts and negatives | from the base | unchanged |
| ledger `working` | the sorted base | `diffs/limbs/{cat}/work/{id}.png` |
| hand-drawn masks next to the sorted base | found | still found (copied beside the working copy) |
| repair failed or found nothing | diffs start from the base | unchanged |

Adds `tests/test_limbs_chain.py` (3 tests). Together with 0001 the factory suite is 175 tests, all passing (187 with 0003).
Tested only with fake detectors and a fake host: no real picture was repainted.

## 0003-lora-check.patch (apply after 0002)

Why LoRA tags seem to have no effect through the factory. Checked on the real code:

1. `txt2img_payload` sends `job["prompt"]` unchanged. A local server that records the request shows the POST to
   `/sdapi/v1/txt2img` carries `<lora:caststyle_xl_epoch08:0.9>` and `<lora:nieva_xl:0.8>` literally, and the
   parameters text saved into the base PNG keeps them.
2. Nothing rewrites the txt2img prompt. `wai17.py` and `pattern_set.py` only build the inpaint stage prompts,
   from the base prompt, and `edit_prompt` keeps `<...>` tags whole. The real planner's stage prompts, body and
   face, all still contain the base LoRA tags; the face pass adds one more, `Expression_Detailer_Illustrious_Lora`.
3. So the tag reaches the WebUI. The WebUI drops a `<lora:name:weight>` whose name it does not list, without an
   error. Colab's launch cell copies only three LoRA files into `models/Lora` (`DefecationIllustV1`,
   `caststyle_xl_epoch08`, `my_lora_fixed_for_webui`), and no sister LoRA (`irito_xl`, `jueri_xl`, `nieva_xl`,
   `seraphina_xl`). A session where those files are absent gives exactly "no effect" and no message. This could not
   be tested against your Colab from here.

What 0003 adds, so the cause shows up instead of staying silent:

* Before posting, the factory asks the chosen host for `/sdapi/v1/loras` and compares every `<lora:...>` /
  `<lyco:...>` name in the job prompt with the names and aliases it lists. `--lora-check error` (default): a job with
  an unknown name stops with `lora_missing` and the list of names, nothing is posted. `warn` posts and notes it.
  `off` skips the check. A host that cannot answer is not blocked.
* After posting, the factory reads the `Lora hashes` the WebUI wrote into the picture it returned. A tag that is
  listed but did not appear gives the warning `lora_not_applied`. This is only a warning, because the format can
  differ between WebUIs. A picture with no infotext is not judged.
* The result is kept in the ledger row (`lora`, `lora_notes`), printed by the `factory` command, and passed on to
  scene-trials, which shows it in each scene's `manifest.json` warnings.

Adds `sd_diff_set/lora_check.py` and `tests/test_lora_check.py` (12 tests). The factory suite is 187 tests with the three patches, and 190 with 0004, all passing. The check needs `--api` on the WebUI (the factory already needs it).

`tools/diagnose_lora.py <api url> --jobs batch.json [--generate]` asks a running WebUI directly: which tag names it
does not list, and, with `--generate`, whether a tiny picture made with the tags differs from one made without and
lists them under `Lora hashes`. Run it against the Colab URL to answer question 3 for certain.

## 0004-keep-base-lora-tags.patch (apply after 0003)

Checked on the real planner before this patch: a base prompt carrying `<lora:caststyle_xl_epoch08:0.9>` and
`<lyco:nieva_xl:0.8>` already kept both tags in all 23 stage prompts, body and face. `edit_prompt` removes tags by
exact text, and no stage's remove list names a LoRA tag, so nothing was dropping them. reForge then parses
`<lora:...>` out of that prompt inside `process_images` and activates the LoRA for the inpaint. The empty script
list the factory uses (to keep ADetailer off) does not turn that off.

0004 makes the keeping explicit. After each stage's prompt is built, every `<lora>` and `<lyco>` tag from the base
is put back, so a stage whose `prompt_remove` names the tag cannot drop it. A tag already present is not copied a
second time. The face prompt is left empty when that stage has no face pass.

`tests/test_lora_prompt.py` checks all 23 stages and a stage that tries to remove the tag.

The diff PNG's parameters are the factory's own text, not the WebUI infotext, so they contain the `<lora:...>` tag
in the first line and do not contain a `Lora hashes` line. Only the masked region is regenerated. The rest stays
the base image.

## 0005-inpaint-keeps-lora.patch (apply after 0004)

The factory does not call the img2img HTTP API. `api_payload.py` is unused, and its prompt is already copied through. Inpaint runs inside reForge: `host.py` builds a processing object and calls `process_images`.

Two things there differed from a manual inpaint.

* The host replaced the always-on scripts with an empty list, so a build that applies networks from a script never got to run it. ADetailer, Regional Prompter and Dynamic Prompts still stay off, and ControlNet and Soft Inpainting run only when the job asks. A script whose name is LoRA, LyCO or extra networks stays.
* reForge skips loading a LoRA when the name list matches the previous call, then img2img samples from `forge_objects_after_applying_lora`, which can still be the model without the LoRA. Before each inpaint whose prompt contains `<lora>` or `<lyco>`, the host clears that hash so the prompt's tags are loaded again. `disable_extra_networks` is set false. The checkpoint, clip skip and VAE overrides do not touch LoRA.

The stage prompt, tags included, is the inpaint prompt. If the WebUI returns `Lora hashes`, they are written onto the diff PNG. If the prompt had tags and no hashes come back, the log says so.

`tests/test_inpaint_lora.py`. With 0001 through 0005 the factory suite is 194 tests, all passing.

## Rebuilding the Colab bundle

`rebuild_bundle.py <extensions/sd-diff-set> [--zip out.zip]` writes `colab/factory_extension.b64` in the
shipped format (a base64 line of a zip whose entries sit under `extension/`; tests, `out/`, `config.json`
and caches are left out). The Colab cell downloads that zip from Drive, so put `--zip` over the Drive file as
well.

The bundle that shipped was already older than the working tree: it had 121 entries and lacked `cloth.yaml`,
`fluid.yaml` and `cloth_detect.py`, and 22 code and preset files differed. The rebuilt one has 127 entries and
carries the 11/13 remodel, 0001, 0002 and 0003. The two bundle tests in `tests/test_factory.py` pass against it.

### What is not done

* The patched files are not in your `C:\work\sd-diff-set`. This environment cannot reach that folder.
* `仕組み.md`, `使い方.md` and the `docs/ファイル説明` pages do not mention the new options.
* Nothing was run with a real GPU or real detectors.
