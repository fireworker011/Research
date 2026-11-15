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

Apply from the `extensions/` folder (the folder that contains `sd-diff-set/`):

```
git apply --check -p1 0001-face-pass-mode.patch
git apply -p1 0001-face-pass-mode.patch
```

### What is verified

* The patch applies to the shared tree and the factory's 156 existing tests still pass.
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

Adds `tests/test_limbs_chain.py` (3 tests). Together with 0001 the factory suite is 175 tests, all passing.
Tested only with fake detectors and a fake host: no real picture was repainted.

## Rebuilding the Colab bundle

`rebuild_bundle.py <extensions/sd-diff-set> [--zip out.zip]` writes `colab/factory_extension.b64` in the
shipped format (a base64 line of a zip whose entries sit under `extension/`; tests, `out/`, `config.json`
and caches are left out). The Colab cell downloads that zip from Drive, so put `--zip` over the Drive file as
well.

The bundle that shipped was already older than the working tree: it had 121 entries and lacked `cloth.yaml`,
`fluid.yaml` and `cloth_detect.py`, and 22 code and preset files differed. The rebuilt one has 127 entries and
carries the 11/13 remodel, 0001 and 0002. The two bundle tests in `tests/test_factory.py` pass against it.

### What is not done

* The patched files are not in your `C:\work\sd-diff-set`. This environment cannot reach that folder.
* `仕組み.md`, `使い方.md` and the `docs/ファイル説明` pages do not mention the new options.
* Nothing was run with a real GPU or real detectors.
