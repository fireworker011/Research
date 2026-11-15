# factory patches

Patches against the 11/13 sd-diff-set copy (`factory-26-20261113`, 26 files, MANIFEST sha256
`69be2044f3e64aae064add2c38a21dd9fd3fda4f2b58390f4bb1e096cc415b19`). They are proposals. Nothing
here has been applied to the factory.

## 0001-face-pass-mode.patch

Adds an opt-in `face_pass` mode to `planner.build_plan`. The default is `required`, which is the
current behavior.

| mode | behavior |
| --- | --- |
| `required` | unchanged: a stage that repaints the face stops with `mask_empty` when no face is found |
| `skip` | the planner drops the face repaint for every stage that has one; each such item gets the warning `face_pass_skipped` |
| `optional` | the face repaint is tried; only `mask_empty` from the face detector is forgiven. The stage continues without the face repaint and the item gets the warning `face_pass_skipped`. Any other error (for example `mask_model_missing`) still stops the stage |

Files: `planner.py` (`build_plan(face_pass=...)`, `PlanItem.face_optional`, `FACE_PASS_MODES`,
bad values raise `bad_face_pass`) and `executor.py` (`_run_item`).

Apply from the `extensions/` folder of the factory:

```
git apply --check -p1 0001-face-pass-mode.patch
git apply -p1 0001-face-pass-mode.patch
```

### What is verified

* The patch applies cleanly to the pristine copy and reproduces the patched tree.
* `planner.py` and `executor.py` compile.
* `check_face_pass.py` runs the real `planner.py`, `executor.py` and `regions.py` with stubs for
  every other module and passes 7 checks: default unchanged, `required` still stops, `skip`,
  `optional` with and without a face, `optional` not hiding other detector errors, bad value refused.

### What is not done

* The value has to reach `build_plan`. `service.run_job`, the job JSON, `pipeline.py` and `cli.py`
  were not in the copy, so that wiring is not written. scene-trials already writes `face_pass` into
  each chain job.
* The factory's own unittest (156 tests) was not run, because most modules are missing from the copy.
* `仕組み.md` and `ファイル説明/sd_diff_set/planner.md` and `executor.md` do not mention the mode yet.
