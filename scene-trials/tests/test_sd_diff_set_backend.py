from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import helpers
from scene_trials.backends import get_backend
from scene_trials.backends.base import ExportingBackend, Role
from scene_trials.backends.sd_diff_set import SdDiffSetBackend
from scene_trials.cli import main
from scene_trials.collector import Status, collect
from scene_trials.errors import BackendError
from scene_trials.layout import Layout
from scene_trials.plan import build_plan
from scene_trials.project import anchor_path, load_project

OPTIONS = """backend:
  name: sd_diff_set
  options:
    work_dir: work
    factory_dir: C:/work/sd-diff-set/extensions/sd-diff-set
    factory_face_pass: {supported}
    colab_api: "{colab}"
    generation: {{sampler_name: Euler a, steps: 28, cfg_scale: 6, model: demoMix_v1}}
"""
CONFIRMED = helpers.PROJECT.replace('adult_confirmed_by: ""', 'adult_confirmed_by: "owner"').replace(
    'adult_confirmed_on: ""', 'adult_confirmed_on: "2026-11-15"'
)


def project_text(*, supported: bool = True, colab: str = "", confirmed: bool = True, face_pass: str = "") -> str:
    base = CONFIRMED if confirmed else helpers.PROJECT
    head = base.split("backend:")[0]
    extra = f"face_pass: {face_pass}\n" if face_pass else ""
    return head + extra + OPTIONS.format(supported=str(supported).lower(), colab=colab)


class Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def plan(self, **kwargs: object):
        project_dir = helpers.make_project(self.root / "proj", project=project_text(**kwargs))  # type: ignore[arg-type]
        self.project_dir = project_dir
        return build_plan(load_project(project_dir))

    def backend(self, plan) -> SdDiffSetBackend:
        backend = get_backend(plan.project.backend, plan.project.root)
        assert isinstance(backend, SdDiffSetBackend)
        return backend


class ExportTests(Fixture):
    def test_factory_jobs_use_the_job_id_and_the_stage_prefix(self) -> None:
        plan = self.plan()
        backend = self.backend(plan)
        self.assertIsInstance(backend, ExportingBackend)
        path = backend.export_batch(plan, plan.batches[0], self.root / "out")
        rows = {row["id"]: row for row in json.loads(path.read_text(encoding="utf-8"))["jobs"]}
        chain = rows["demo-lantern_light-t1"]
        self.assertEqual(chain["stages"], ["dim", "bright", "flare"])
        self.assertNotIn("face_pass", chain)
        for key in ("prompt", "negative_prompt", "sampler_name", "steps", "cfg_scale", "width", "height", "model"):
            self.assertIn(key, chain)
        self.assertEqual(rows["demo-S01_standing_01-t1"]["stages"], ["none"])

    def test_face_pass_is_written_only_when_the_factory_can_honor_it(self) -> None:
        text = project_text(supported=True)
        chains = helpers.CHAINS + "    face_pass: skip\n"
        project_dir = helpers.make_project(self.root / "a", project=text, chains=chains)
        plan = build_plan(load_project(project_dir))
        rows = json.loads(self.backend(plan).export_batch(plan, plan.batches[0], self.root / "o").read_text())["jobs"]
        self.assertEqual(next(r for r in rows if r["id"].startswith("demo-lantern"))["face_pass"], "skip")

        project_dir = helpers.make_project(self.root / "b", project=project_text(supported=False), chains=chains)
        plan = build_plan(load_project(project_dir))
        with self.assertRaises(BackendError) as caught:
            self.backend(plan).export_batch(plan, plan.batches[0], self.root / "o2")
        self.assertEqual(caught.exception.code, "face_pass_unsupported")

    def test_options_are_validated(self) -> None:
        with self.assertRaises(BackendError):
            SdDiffSetBackend({"generation": {}})
        with self.assertRaises(BackendError):
            SdDiffSetBackend({"work_dir": "w"})
        with self.assertRaises(BackendError):
            SdDiffSetBackend({"work_dir": "w", "generation": {"steps": 20}})
        with self.assertRaises(BackendError):
            SdDiffSetBackend(
                {"work_dir": "w", "generation": {"sampler_name": "a", "steps": 1, "cfg_scale": 1, "model": "m", "x": 1}}
            )
        with self.assertRaises(BackendError):
            SdDiffSetBackend(
                {"work_dir": "w", "finish": "poster", "generation": {"sampler_name": "a", "steps": 1, "cfg_scale": 1, "model": "m"}}
            )

    def test_job_ids_must_not_look_like_factory_files(self) -> None:
        text = project_text().replace("project: demo", "project: x_diff-y")
        project_dir = helpers.make_project(self.root / "p", project=text)
        plan = build_plan(load_project(project_dir))
        with self.assertRaises(BackendError) as caught:
            self.backend(plan).export_batch(plan, plan.batches[0], self.root / "o")
        self.assertEqual(caught.exception.code, "job_id_reserved")

    def test_lora_check_flag_is_written_only_when_asked(self) -> None:
        plan = self.plan()
        files = {batch.batch_id: self.root / f"{batch.batch_id}.json" for batch in plan.batches}
        self.assertNotIn("--lora-check", "\n".join(self.backend(plan).run_commands(plan, "sh", files)))
        text = project_text().replace("factory_face_pass: true", "factory_face_pass: true\n    lora_check: warn")
        project_dir = helpers.make_project(self.root / "lc", project=text)
        plan = build_plan(load_project(project_dir))
        self.assertIn("--lora-check warn", "\n".join(self.backend(plan).run_commands(plan, "sh", files)))
        with self.assertRaises(BackendError):
            SdDiffSetBackend(
                {"work_dir": "w", "lora_check": "maybe", "generation": {"sampler_name": "a", "steps": 1, "cfg_scale": 1, "model": "m"}}
            )

    def test_limbs_off_is_the_only_way_the_script_skips_them(self) -> None:
        plan = self.plan()
        files = {batch.batch_id: self.root / f"{batch.batch_id}.json" for batch in plan.batches}
        self.assertNotIn("--no-limbs", "\n".join(self.backend(plan).run_commands(plan, "sh", files)))
        text = project_text().replace("factory_face_pass: true", "factory_face_pass: true\n    limbs: false")
        project_dir = helpers.make_project(self.root / "limbs", project=text)
        plan = build_plan(load_project(project_dir))
        self.assertIn("--no-limbs", "\n".join(self.backend(plan).run_commands(plan, "sh", files)))
        with self.assertRaises(BackendError):
            SdDiffSetBackend(
                {"work_dir": "w", "limbs": "no", "generation": {"sampler_name": "a", "steps": 1, "cfg_scale": 1, "model": "m"}}
            )

    def test_run_commands_quote_per_shell_and_carry_the_declaration(self) -> None:
        plan = self.plan(colab="https://example.gradio.live")
        backend = self.backend(plan)
        files = {batch.batch_id: self.root / f"{batch.batch_id}.json" for batch in plan.batches}
        sh = "\n".join(backend.run_commands(plan, "sh", files))
        ps1 = "\n".join(backend.run_commands(plan, "ps1", files))
        for text in (sh, ps1):
            self.assertIn("sd_diff_set.cli factory", text)
            self.assertIn("--adult-ok --run --once", text)
            self.assertIn("--colab-api", text)
            self.assertEqual(text.count("# batch"), 3)
        self.assertTrue(sh.startswith("cd "))
        self.assertTrue(ps1.startswith("Set-Location '"))
        self.assertIn("--jobs '", ps1)


def _ledger(work: Path, rows: dict[str, dict[str, object]]) -> None:
    folder = work / "diffs"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "pipeline.json").write_text(json.dumps({"version": 1, "items": rows}), encoding="utf-8")


def _write(path: Path) -> Path:
    return helpers.write_image(path)


class ProducedFilesTests(Fixture):
    def tree(self, plan, *, stem: str = "demo-lantern_light-t1") -> dict[str, Path]:
        work = self.project_dir / "work"
        category = "lantern"
        sorted_png = _write(work / "sorted" / category / f"{stem}.png")
        clear = _write(work / "sorted" / category / f"{stem}.transparent.png")
        folder = work / "diffs" / category / stem
        items = []
        for index, (variant, status, code) in enumerate(
            (("dim", "ok", None), ("bright", "ok", None), ("flare", "error", "mask_empty")), start=1
        ):
            output = folder / f"{stem}_{index:03d}_diff-{category}-{variant}.png"
            if status == "ok":
                _write(output)
                _write(output.with_name(output.stem + ".transparent.png"))
                _write(output.with_name(output.stem + ".mask.png"))
            items.append(
                {
                    "variant": variant,
                    "status": status,
                    "error_code": code,
                    "path": str(output) if status == "ok" else None,
                    "mask_file": str(output.with_name(output.stem + ".mask.png")) if status == "ok" else None,
                    "warnings": ["face_pass_skipped: x"] if variant == "dim" else [],
                }
            )
        manifest = folder / "manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({"items": items}), encoding="utf-8")
        _ledger(
            work,
            {
                "aaa": {
                    "source": str(work / "generated" / f"{stem}.png"),
                    "sorted": str(sorted_png),
                    "category": category,
                    "status": "error",
                    "error_code": "mask_empty",
                    "manifest": str(manifest),
                    "transparent": str(clear),
                    "working": str(sorted_png),
                    "lora_notes": ["lora_missing: ghost"],
                }
            },
        )
        return {"sorted": sorted_png, "manifest": manifest}

    def test_stage_files_failures_and_warnings(self) -> None:
        plan = self.plan()
        self.tree(plan)
        output = self.backend(plan).produced_files(plan)
        files = [f for f in output.files if f.job_id == "demo-lantern_light-t1"]
        by = {(f.role, f.stage): f for f in files}
        self.assertTrue(by[(Role.BASE, None)].ok)
        self.assertTrue(by[(Role.STAGE, "bright")].ok)
        self.assertEqual(by[(Role.STAGE, "flare")].error_code, "mask_empty")
        self.assertFalse(by[(Role.STAGE, "flare")].ok)
        self.assertIn(Role.TRANSPARENT, {f.role for f in files})
        self.assertIn((Role.MASK, "bright"), by)
        self.assertTrue(any("face_pass_skipped" in w for w in by[(Role.STAGE, "dim")].warnings))
        self.assertIn("lora_missing: ghost", by[(Role.STAGE, "bright")].warnings)
        self.assertTrue(any(w.startswith("paint:") for w in by[(Role.BASE, None)].warnings))
        self.assertEqual([f for f in output.files if f.job_id.endswith("-t2")], [])

    def test_collector_turns_them_into_scene_results(self) -> None:
        plan = self.plan()
        self.tree(plan)
        report = collect(plan, self.backend(plan).produced_files(plan), backend_name="sd_diff_set")
        by = {(r.scene_id, r.trial): r for r in report.results}
        self.assertEqual(by[("S03_holding_01", 1)].status, Status.OK)
        self.assertEqual(by[("S04_holding_02", 1)].status, Status.OK)
        failed = by[("S05_holding_03", 1)]
        self.assertEqual((failed.status, failed.error_code), (Status.FAILED, "mask_empty"))
        self.assertEqual(by[("S03_holding_01", 2)].status, Status.MISSING)

    def test_paths_from_another_machine_are_found_under_work_dir(self) -> None:
        plan = self.plan()
        paths = self.tree(plan)
        ledger_path = self.project_dir / "work" / "diffs" / "pipeline.json"
        text = ledger_path.read_text(encoding="utf-8").replace(str(self.project_dir / "work"), "C:\\\\sd-out\\\\auto")
        ledger_path.write_text(text.replace("/sorted/", "\\\\sorted\\\\").replace("/generated/", "\\\\generated\\\\"), encoding="utf-8")
        output = self.backend(plan).produced_files(plan)
        base = next(f for f in output.files if f.role is Role.BASE)
        self.assertEqual(base.path, paths["sorted"])

    def test_lora_notes_from_the_ledger_reach_the_scene_warnings(self) -> None:
        plan = self.plan()
        work = self.project_dir / "work"
        stem = "demo-S01_standing_01-t1"
        _ledger(
            work,
            {
                "ccc": {
                    "source": str(work / "generated" / f"{stem}.png"),
                    "sorted": str(_write(work / "sorted" / "expr4" / f"{stem}.png")),
                    "category": "expr4",
                    "status": "ok",
                    "lora_notes": ["lora_not_applied: the picture has no Lora hashes: nieva_xl"],
                }
            },
        )
        output = self.backend(plan).produced_files(plan)
        base = next(f for f in output.files if f.role is Role.BASE)
        self.assertIn("lora_not_applied", " ".join(base.warnings))
        report = collect(plan, output, backend_name="sd_diff_set")
        solo = next(r for r in report.results if r.scene_id == "S01_standing_01" and r.trial == 1)
        self.assertTrue(any("lora_not_applied" in w for w in solo.warnings))

    def test_refused_row_is_a_failed_base(self) -> None:
        plan = self.plan()
        work = self.project_dir / "work"
        stem = "demo-S01_standing_01-t1"
        _ledger(
            work,
            {
                "bbb": {
                    "source": str(work / "generated" / f"{stem}.png"),
                    "sorted": str(_write(work / "sorted" / "refused" / f"{stem}.png")),
                    "category": "refused",
                    "status": "refused",
                    "error_code": "cast_excluded",
                }
            },
        )
        output = self.backend(plan).produced_files(plan)
        base = next(f for f in output.files if f.job_id == stem)
        self.assertEqual((base.ok, base.error_code), (False, "cast_excluded"))
        report = collect(plan, output, backend_name="sd_diff_set")
        solo = next(r for r in report.results if r.scene_id == "S01_standing_01" and r.trial == 1)
        self.assertEqual((solo.status, solo.error_code), (Status.FAILED, "cast_excluded"))

    def test_hash_suffixed_duplicates_match_and_are_noted(self) -> None:
        plan = self.plan()
        work = self.project_dir / "work"
        stem = "demo-S01_standing_01-t1"
        rows = {}
        for key, name in (("a", stem), ("b", f"{stem}-1a2b3c4d")):
            rows[key] = {
                "source": str(work / "generated" / f"{name}.png"),
                "sorted": str(_write(work / "sorted" / "expr4" / f"{name}.png")),
                "category": "expr4",
                "status": "ok",
            }
        _ledger(work, rows)
        output = self.backend(plan).produced_files(plan)
        self.assertTrue(any(note.startswith("duplicate_rows") for note in output.notes))
        base = next(f for f in output.files if f.role is Role.BASE)
        self.assertTrue(base.path.name.startswith(f"{stem}-1a2b3c4d"))

    def test_missing_ledger_is_an_error(self) -> None:
        plan = self.plan()
        with self.assertRaises(BackendError) as caught:
            self.backend(plan).produced_files(plan)
        self.assertEqual(caught.exception.code, "ledger_missing")


class CliExportTests(Fixture):
    def run_cli(self, *args: str) -> tuple[int, str]:
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = main([args[0], "--project", str(self.project_dir), *args[1:]])
        return code, err.getvalue()

    def test_export_needs_the_declaration_then_writes_factory_files(self) -> None:
        self.plan(confirmed=False)
        code, err = self.run_cli("export")
        self.assertEqual(code, 2)
        self.assertIn("adult_not_confirmed", err)
        self.plan(confirmed=True)
        code, _ = self.run_cli("export")
        self.assertEqual(code, 0)
        meta = Layout(load_project(self.project_dir)).meta()
        self.assertEqual(
            sorted(path.name for path in (meta / "sd_diff_set").glob("*.json")), ["t1-b1.json", "t2-b1.json", "t3-b1.json"]
        )
        self.assertIn("--adult-ok", (meta / "sd_diff_set_run.sh").read_text(encoding="utf-8"))
        self.assertTrue((meta / "sd_diff_set_run.ps1").is_file())

    def test_import_only_projects_export_exactly_as_before(self) -> None:
        project_dir = helpers.make_project(self.root / "io", project=CONFIRMED)
        self.project_dir = project_dir
        code, _ = self.run_cli("export")
        self.assertEqual(code, 0)
        meta = Layout(load_project(project_dir)).meta()
        self.assertFalse((meta / "sd_diff_set").exists())


if __name__ == "__main__":
    unittest.main()


class PathTests(unittest.TestCase):
    def test_drive_paths_stay_as_written_and_relative_ones_hang_off_the_project(self) -> None:
        base = Path("/proj")
        self.assertEqual(str(anchor_path(Path("C:/sd-out/auto"), base)).replace("\\", "/"), "C:/sd-out/auto")
        self.assertEqual(anchor_path(Path("work"), base), Path("/proj/work"))
        self.assertEqual(anchor_path(Path("/abs"), base), Path("/abs"))
        self.assertEqual(anchor_path(Path("work"), None), Path("work"))
