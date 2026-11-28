from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers
from scene_trials.chains import load_chain_specs, resolve_chains
from scene_trials.errors import ConfigError
from scene_trials.project import OUT_ROOT_ENV, load_project
from scene_trials.scenes import find_scene, load_scenes


class ProjectTests(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop(OUT_ROOT_ENV, None)

    def test_loads_and_resolves_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = load_project(helpers.make_project(Path(tmp) / "p"))
            self.assertEqual(project.name, "demo")
            self.assertEqual(project.trial_count, 3)
            self.assertEqual((project.width, project.height), (1024, 1344))
            self.assertTrue(str(project.project_out).endswith(os.path.join("out", "demo")))

    def test_unknown_key_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = helpers.make_project(Path(tmp) / "p", project=helpers.PROJECT + "typo_key: 1\n")
            with self.assertRaises(ConfigError) as caught:
                load_project(root)
            self.assertEqual(caught.exception.code, "unknown_key")

    def test_reserved_out_root_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            text = helpers.PROJECT.replace("out_root: out", "out_root: out/Picture/CG")
            with self.assertRaises(ConfigError) as caught:
                load_project(helpers.make_project(Path(tmp) / "p", project=text))
            self.assertEqual(caught.exception.code, "out_root_forbidden")

    def test_env_overrides_out_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = helpers.make_project(Path(tmp) / "p")
            os.environ[OUT_ROOT_ENV] = str(Path(tmp) / "elsewhere")
            project = load_project(root)
            self.assertEqual(project.out_root, (Path(tmp) / "elsewhere").resolve())

    def test_windows_path_on_linux_needs_override(self) -> None:
        if os.name == "nt":
            self.skipTest("Windows path is valid here")
        with tempfile.TemporaryDirectory() as tmp:
            text = helpers.PROJECT.replace("out_root: out", "out_root: C:/sd-out/scenes")
            with self.assertRaises(ConfigError) as caught:
                load_project(helpers.make_project(Path(tmp) / "p", project=text))
            self.assertEqual(caught.exception.code, "out_root_platform")


class SceneChainTests(unittest.TestCase):
    def _load(self, tmp: str, **kwargs: str):
        project = load_project(helpers.make_project(Path(tmp) / "p", **kwargs))
        return project, load_scenes(project)

    def test_scene_ids_and_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _project, scenes = self._load(tmp)
            self.assertEqual(scenes[0].scene_id, "S01_standing_01")
            self.assertEqual(scenes[3].section, "lantern")
            self.assertEqual(find_scene(scenes, 4).scene_id, "S04_holding_02")
            self.assertEqual(find_scene(scenes, "S04_holding_02").row, 4)

    def test_non_ascii_section_needs_a_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenes = helpers.SCENES.replace("lantern,dim", "灯,dim")
            project = load_project(helpers.make_project(Path(tmp) / "p", scenes=scenes))
            with self.assertRaises(ConfigError) as caught:
                load_scenes(project)
            self.assertEqual(caught.exception.code, "section_unmapped")

    def test_chain_asks_only_for_stages_up_to_the_last_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, scenes = self._load(tmp)
            chain = resolve_chains(load_chain_specs(project.chains_path), scenes)[0]
            self.assertEqual(chain.stages, ("dim", "bright", "flare"))
            narrow = helpers.CHAINS.replace("scenes: {3: dim, 4: bright, 5: flare}", "scenes: {3: dim, 4: bright}")
            project2, scenes2 = self._load(tmp + "/b", chains=narrow)
            chain2 = resolve_chains(load_chain_specs(project2.chains_path), scenes2)[0]
            self.assertEqual(chain2.stages, ("dim", "bright"))

    def test_chain_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_stage = helpers.CHAINS.replace("4: bright", "4: nope")
            project, scenes = self._load(tmp, chains=bad_stage)
            with self.assertRaises(ConfigError) as caught:
                resolve_chains(load_chain_specs(project.chains_path), scenes)
            self.assertEqual(caught.exception.code, "chain_stage_unknown")

            base_outside = helpers.CHAINS.replace("base: 4", "base: 1")
            project, scenes = self._load(tmp + "/b", chains=base_outside)
            with self.assertRaises(ConfigError) as caught:
                resolve_chains(load_chain_specs(project.chains_path), scenes)
            self.assertEqual(caught.exception.code, "chain_base_not_member")


if __name__ == "__main__":
    unittest.main()
