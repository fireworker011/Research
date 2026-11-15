from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import helpers
from scene_trials.backends import get_backend
from scene_trials.backends.import_only import ImportOnlyBackend
from scene_trials.cli import main
from scene_trials.collector import Status, collect, find_result
from scene_trials.cutout_cmds import build_cutout_commands
from scene_trials.errors import BackendError, ConfigError, SceneTrialsError
from scene_trials.layout import Layout
from scene_trials.plan import build_plan
from scene_trials.project import BackendConfig, load_project
from scene_trials.select import finalize, make_sheet, read_selection, set_pick

OPAQUE = (200, 30, 30, 255)
CLEAR = (200, 30, 30, 0)


class Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.project_dir = helpers.make_project(self.root / "proj")
        self.incoming = self.project_dir / "incoming"
        self.plan = build_plan(load_project(self.project_dir))

    def backend(self) -> ImportOnlyBackend:
        return ImportOnlyBackend({"source_dir": str(self.incoming)}, self.project_dir)

    def drop(self, name: str, color: tuple[int, int, int, int] = OPAQUE) -> Path:
        return helpers.write_image(self.incoming / name, color)

    def run_collect(self, overwrite: bool = False):
        return collect(self.plan, self.backend().produced_files(self.plan), backend_name="import_only", overwrite=overwrite)


class ImportCollectTests(Fixture):
    def test_chain_and_solo_files_land_in_the_layout(self) -> None:
        self.drop("S04_holding_02__t1.png")
        self.drop("S03_holding_01__t1__dim.png")
        self.drop("S04_holding_02__t1__bright.png")
        self.drop("S04_holding_02__t1__bright.transparent.png", CLEAR)
        self.drop("S04_holding_02__t1__bright.mask.png")
        self.drop("S01_standing_01__t1.png")
        report = self.run_collect()
        layout = Layout(self.plan.project)

        solo = layout.trial_dir("sprite", "S01_standing_01", 1)
        self.assertIsNotNone(find_result(solo))
        bright = layout.trial_dir("lantern", "S04_holding_02", 1)
        self.assertTrue((bright / "result.png").is_file())
        self.assertTrue((bright / "base.png").is_file())
        self.assertTrue((bright / "result.transparent.png").is_file())
        self.assertTrue((bright / "masks" / "result.mask.png").is_file())
        manifest = json.loads((bright / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], Status.OK)
        self.assertEqual(manifest["stage"], "bright")
        self.assertIn("negative", manifest["prompt"])
        chain_dir = layout.chain_trial_dir("lantern_light", 1)
        self.assertTrue((chain_dir / "stage_dim.png").is_file())
        self.assertTrue((chain_dir / "job.json").is_file())

        statuses = {(r.scene_id, r.trial): r.status for r in report.results}
        self.assertEqual(statuses[("S01_standing_01", 1)], Status.OK)
        self.assertEqual(statuses[("S05_holding_03", 1)], Status.MISSING)
        self.assertEqual(statuses[("S01_standing_01", 2)], Status.MISSING)
        self.assertEqual(report.counts()[Status.OK], 3)

    def test_failed_stage_is_reported_not_copied(self) -> None:
        self.drop("S04_holding_02__t1.png")
        self.drop("S03_holding_01__t1__dim.png")
        index = self.incoming / "index.csv"
        index.write_text(
            "path,scene_id,trial,role,stage,ok,error_code\n"
            "S04_holding_02__t1__bright.png,S04_holding_02,1,stage,bright,false,mask_empty\n",
            encoding="utf-8",
        )
        self.drop("S04_holding_02__t1__bright.png")
        backend = ImportOnlyBackend({"source_dir": str(self.incoming), "index_csv": str(index)})
        report = collect(self.plan, backend.produced_files(self.plan), backend_name="import_only")
        failed = next(r for r in report.results if r.scene_id == "S04_holding_02" and r.trial == 1)
        self.assertEqual((failed.status, failed.error_code), (Status.FAILED, "mask_empty"))
        trial_dir = Layout(self.plan.project).trial_dir("lantern", "S04_holding_02", 1)
        self.assertIsNone(find_result(trial_dir))

    def test_unknown_names_and_stages_are_noted(self) -> None:
        self.drop("random_name.png")
        self.drop("S99_nope__t1.png")
        self.drop("S04_holding_02__t1__ghost.png")
        self.drop("S04_holding_02__t7.png")
        output = self.backend().produced_files(self.plan)
        self.assertEqual(output.files, [])
        kinds = sorted(note.split(":")[0] for note in output.notes)
        self.assertEqual(kinds, ["unknown_scene", "unknown_scene", "unknown_stage", "unmatched"])

    def test_recollect_is_idempotent_and_conflicts_are_kept(self) -> None:
        source = self.drop("S01_standing_01__t1.png")
        self.run_collect()
        again = self.run_collect()
        self.assertEqual(again.conflicts, [])
        helpers.write_image(source, (1, 2, 3, 255))
        clash = self.run_collect()
        self.assertEqual(len(clash.conflicts), 2)
        self.assertTrue(any("_chains" in line for line in clash.conflicts))
        result = Layout(self.plan.project).trial_dir("sprite", "S01_standing_01", 1) / "result.png"
        self.assertNotEqual(result.read_bytes(), source.read_bytes())
        self.run_collect(overwrite=True)
        self.assertEqual(result.read_bytes(), source.read_bytes())

    def test_relative_source_dir_is_anchored_to_the_project(self) -> None:
        backend = get_backend(load_project(self.project_dir).backend, self.project_dir)
        self.assertEqual(Path(backend.source_dir).resolve(), (self.project_dir / "incoming").resolve())

    def test_backend_registry(self) -> None:
        with self.assertRaises(BackendError) as caught:
            get_backend(BackendConfig(name="sd_diff_set"), self.project_dir)
        self.assertEqual(caught.exception.code, "backend_unavailable")
        with self.assertRaises(BackendError):
            get_backend(BackendConfig(name="import_only"), self.project_dir)
        with self.assertRaises(BackendError):
            get_backend(BackendConfig(name="nothing"), self.project_dir)


class SelectCutoutTests(Fixture):
    def prepare(self) -> None:
        self.drop("S01_standing_01__t1.png")
        self.drop("S01_standing_01__t2.png", (10, 200, 10, 255))
        self.drop("S01_standing_01__t3.png", (10, 10, 200, 255))
        self.drop("S02_standing_02__t1.png")
        self.drop("S02_standing_02__t1.transparent.png", CLEAR)
        self.run_collect()

    def test_pick_validates_and_persists(self) -> None:
        self.prepare()
        pick = set_pick(self.plan, "S01_standing_01", 2, "best hands")
        self.assertEqual((pick.trial, pick.note), (2, "best hands"))
        stored = read_selection(Layout(self.plan.project).selection_csv())
        self.assertEqual(stored["S01_standing_01"].trial, 2)
        with self.assertRaises(SceneTrialsError):
            set_pick(self.plan, "S02_standing_02", 3)
        with self.assertRaises(SceneTrialsError):
            set_pick(self.plan, "S02_standing_02", 9)
        with self.assertRaises(SceneTrialsError):
            set_pick(self.plan, "S77", 1)

    def test_sheet_is_written_even_with_missing_trials(self) -> None:
        self.prepare()
        path = make_sheet(self.plan, "S02_standing_02")
        self.assertTrue(path.is_file())
        self.assertEqual(path.parent.name, "sprite")

    def test_finalize_and_cutout_commands(self) -> None:
        self.prepare()
        set_pick(self.plan, "S01_standing_01", 2)
        set_pick(self.plan, "S02_standing_02", 1)
        layout = Layout(self.plan.project)
        done = finalize(self.plan, read_selection(layout.selection_csv()))
        self.assertEqual(len(done), 2)
        self.assertTrue((layout.selected_dir("sprite", "S01_standing_01") / "S01_standing_01.png").is_file())
        result = build_cutout_commands(self.plan, done)
        self.assertEqual(len(result.commands["ps1"]), 1)
        self.assertEqual(len(result.commands["sh"]), 1)
        self.assertIn("S01_standing_01.png", result.commands["sh"][0])
        self.assertTrue(result.commands["ps1"][0].startswith("tool cutout --input '"))
        self.assertEqual(len(result.skipped), 1)
        self.assertTrue(all(path.is_file() for path in result.files))

    def test_template_without_known_placeholder_fails_clearly(self) -> None:
        self.prepare()
        set_pick(self.plan, "S01_standing_01", 1)
        text = helpers.PROJECT.replace("tool cutout --input {input}", "tool {nope}")
        project_dir = helpers.make_project(self.root / "bad", project=text)
        plan = build_plan(load_project(project_dir))
        picks = {"S01_standing_01": read_selection(Layout(self.plan.project).selection_csv())["S01_standing_01"]}
        helpers.write_image(
            Layout(plan.project).trial_dir("sprite", "S01_standing_01", 1) / "result.png"
        )
        with self.assertRaises(ConfigError) as caught:
            build_cutout_commands(plan, finalize(plan, picks))
        self.assertEqual(caught.exception.code, "cutout_template_bad")


class CliTests(Fixture):
    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main([*args, "--project", str(self.project_dir)] if args[0] not in ("pick",) else [args[0], "--project", str(self.project_dir), *args[1:]])
        return code, out.getvalue(), err.getvalue()

    def test_export_needs_adult_confirmation(self) -> None:
        code, _out, err = self.run_cli("export")
        self.assertEqual(code, 2)
        self.assertIn("adult_not_confirmed", err)
        confirmed = helpers.PROJECT.replace('adult_confirmed_by: ""', 'adult_confirmed_by: "owner"').replace(
            'adult_confirmed_on: ""', 'adult_confirmed_on: "2026-11-15"'
        )
        helpers.make_project(self.project_dir, project=confirmed)
        code, out, _err = self.run_cli("export")
        self.assertEqual(code, 0, out)
        batches = sorted((Layout(load_project(self.project_dir)).meta() / "batches").glob("*.json"))
        self.assertEqual([path.stem for path in batches], ["t1-b1", "t2-b1", "t3-b1"])
        payload = json.loads(batches[0].read_text(encoding="utf-8"))
        self.assertEqual(payload["jobs"][0]["trial"], 1)

    def test_end_to_end(self) -> None:
        self.drop("S01_standing_01__t1.png")
        self.drop("S01_standing_01__t2.png")
        code, out, _err = self.run_cli("plan")
        self.assertEqual(code, 0)
        self.assertIn("4 bases per trial", out)
        code, out, _err = self.run_cli("collect")
        self.assertEqual(code, 0)
        self.assertIn("ok 2", out)
        self.assertEqual(self.run_cli("sheet")[0], 0)
        self.assertEqual(self.run_cli("pick", "S01_standing_01", "2")[0], 0)
        self.assertEqual(self.run_cli("finalize")[0], 0)
        code, out, _err = self.run_cli("cutout-cmds")
        self.assertEqual(code, 0)
        self.assertIn("not executed", out)

    def test_plan_errors_exit_nonzero(self) -> None:
        scenes = helpers.SCENES.replace("waving", "waving, loli")
        helpers.make_project(self.project_dir, scenes=scenes)
        code, _out, err = self.run_cli("plan")
        self.assertEqual(code, 2)
        self.assertIn("cast_excluded", err)


if __name__ == "__main__":
    unittest.main()
