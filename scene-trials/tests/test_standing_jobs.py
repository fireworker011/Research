from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scene_trials.errors import ConfigError
from scene_trials.resources import load_loras
from scene_trials.standing_jobs import (
    POSE_EDITS,
    build_standing_jobs,
    load_standing_settings,
    write_jobs,
)

PROJECT = Path(__file__).resolve().parents[1] / "projects" / "pronant" / "project.yaml"
SCENES = """id,category,subcategory,char,diff_stage
001,立ち絵,通常,irito,01_通常
002,立ち絵,恥じらい,jueri,04_恥じらい
003,立ち絵,後ろ姿,nieva,05_後ろ
004,アナル,立ちバック,irito,02_挿入中
005,立ち絵,通常,sora,01_通常
006,立ち絵,通常,seraphina,01_通常
"""
TEMPLATES = """category,subcategory,positive_prompt,negative_prompt
立ち絵,通常,"masterpiece, caststyle_xl, {irito_xl|jueri_xl|nieva_xl|seraphina_xl}, dynamic pose, neutral expression, full body, landscape composition, horizontal framing",low quality
立ち絵,微笑み,"masterpiece, caststyle_xl, {irito_xl|jueri_xl|nieva_xl|seraphina_xl}, gentle smile, slight head tilt, full body, landscape composition",low quality
立ち絵,後ろ姿,"masterpiece, caststyle_xl, {irito_xl|jueri_xl|nieva_xl|seraphina_xl}, from behind, ass focus, full body, landscape composition",low quality
フェラ,フェラ中,"masterpiece, caststyle_xl, {irito_xl|jueri_xl}, blowjob",low quality
"""


class StandingJobTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.scenes = self.root / "scenes.csv"
        self.templates = self.root / "templates.csv"
        self.scenes.write_text(SCENES, encoding="utf-8")
        self.templates.write_text(TEMPLATES, encoding="utf-8")
        settings, loras_path = load_standing_settings(PROJECT)
        self.settings = settings
        self.loras = load_loras(loras_path)

    def build(self, scenes: str | None = None):
        if scenes is not None:
            self.scenes.write_text(scenes, encoding="utf-8")
        return build_standing_jobs(self.scenes, self.templates, loras=self.loras, settings=self.settings)

    def test_standing_rows_get_the_character_lora_and_no_pattern_stages(self) -> None:
        jobs, skipped = self.build()
        self.assertEqual(skipped, 1)
        self.assertEqual([job["id"] for job in jobs], ["standing-irito-01", "standing-jueri-04", "standing-nieva-05", "standing-seraphina-01"])
        by_id = {job["id"]: job for job in jobs}
        irito = by_id["standing-irito-01"]["prompt"]
        self.assertIn("<lora:caststyle_xl_epoch08:0.9>", irito)
        self.assertIn("<lora:irito_xl:0.8>", irito)
        self.assertNotIn("{", irito)
        self.assertNotIn("landscape composition", irito)
        self.assertNotIn("horizontal framing", irito)
        self.assertIn("(mature female:1.2)", irito)
        self.assertIn("neutral expression", irito)
        self.assertIn("child", by_id["standing-irito-01"]["negative_prompt"])
        self.assertEqual(by_id["standing-jueri-04"]["stages"], ["none"])
        self.assertIn("<lora:jueri_xl:0.8>", by_id["standing-jueri-04"]["prompt"])
        self.assertIn("blush", by_id["standing-jueri-04"]["prompt"])
        self.assertNotIn("gentle smile", by_id["standing-jueri-04"]["prompt"])
        self.assertIn("from behind", by_id["standing-nieva-05"]["prompt"])
        self.assertIn("<lora:nieva_xl:0.8>", by_id["standing-nieva-05"]["prompt"])
        self.assertEqual(by_id["standing-irito-01"]["sampler_name"], "Euler a")
        self.assertEqual(by_id["standing-irito-01"]["steps"], 28)
        self.assertEqual(by_id["standing-irito-01"]["cfg_scale"], 6)
        self.assertEqual(by_id["standing-irito-01"]["width"], 1024)
        self.assertEqual(by_id["standing-irito-01"]["height"], 1344)
        self.assertEqual(by_id["standing-irito-01"]["clip_skip"], 2)
        self.assertEqual(by_id["standing-irito-01"]["model"], "2883731_waiIllustriousSDXL_v170.safetensors")

    def test_a_pose_edit_keeps_the_base_template(self) -> None:
        text = SCENES + "007,立ち絵,腰突き出し,irito,07_腰出し\n008,立ち絵,横向き,seraphina,06_横\n"
        jobs, _skipped = self.build(text)
        hip = next(job for job in jobs if job["id"] == "standing-irito-07")
        side = next(job for job in jobs if job["id"] == "standing-seraphina-06")
        self.assertIn("from behind", hip["prompt"])
        self.assertIn("ass focus", hip["prompt"])
        self.assertIn("bent over", hip["prompt"])
        self.assertIn("from side", side["prompt"])
        self.assertNotIn("neutral expression", side["prompt"])
        self.assertIn("<lora:seraphina_xl:0.8>", side["prompt"])

    def test_an_unknown_pose_or_character_is_refused(self) -> None:
        with self.assertRaises(ConfigError) as unknown_pose:
            self.build(SCENES + "009,立ち絵,未定,irito,11_未定\n")
        self.assertEqual(unknown_pose.exception.code, "template_missing")
        with self.assertRaises(ConfigError) as unknown_char:
            self.build("id,category,subcategory,char,diff_stage\n1,立ち絵,通常,mina,01_通常\n")
        self.assertEqual(unknown_char.exception.code, "standing_char")

    def test_the_pose_table_only_names_templates_the_csv_is_expected_to_have(self) -> None:
        self.assertEqual(
            {edit.base for edit in POSE_EDITS.values()},
            {"通常", "微笑み", "後ろ姿"},
        )

    def test_write_jobs_keeps_the_factory_keys_in_order(self) -> None:
        jobs, _skipped = self.build()
        dest = self.root / "standing.json"
        write_jobs(dest, jobs)
        payload = json.loads(dest.read_text(encoding="utf-8"))
        self.assertEqual(list(payload["jobs"][0]), list(jobs[0]))
        self.assertNotIn("anal", dest.read_text(encoding="utf-8").split("jobs")[0])
