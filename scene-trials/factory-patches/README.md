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
* It adds `tests/test_face_pass.py` with 16 tests (172 in total, all passing). On the unpatched tree 14 of
  those 16 fail, so they do exercise the change.
* `integration/check_sd_diff_set.py` runs the real factory end to end with only the GPU parts replaced,
  against both the patched and the unpatched tree.
* Weights: the factory's tests need the four detector files to exist. They do not read them. Point
  `SD_DIFF_WEIGHTS_DIR` at a folder of empty files when running on a machine without the real weights.

### What is not done

* `colab/factory_extension.b64` is a bundle of the old sources. Rebuild it before Colab uses the patch.
* `仕組み.md`, `使い方.md` and the `docs/ファイル説明` pages do not mention the new options.
* Nothing was run with a real GPU or real detectors.

## Known issue, not patched

`Pipeline._produced_image` reads `item["output_path"]`, but the manifest item key is `"path"`
(`manifest.item_payload`). So the hands and feet repairs are never chained: each runs on the original
sorted base, the ledger's `working` stays equal to `sorted`, and the diffs start from the unrepaired base.
No test covers it. A one-word fix would change output folder names (the diff folder would be named after the
repaired file), so it needs your decision. scene-trials reads `manifest` and `working` from the ledger, so it
works either way.
