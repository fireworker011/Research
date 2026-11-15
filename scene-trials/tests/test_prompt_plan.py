from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import helpers
from scene_trials.errors import ConfigError
from scene_trials.plan import JobKind, build_plan
from scene_trials.project import load_project
from scene_trials.prompt import expand_braces, resolve_prompt
from scene_trials.resources import LoraEntry, NegativeSet
from scene_trials.tags import split_tags


def _plan(tmp: str, **kwargs: str):
    return build_plan(load_project(helpers.make_project(Path(tmp) / "p", **kwargs)))


class BraceTests(unittest.TestCase):
    def test_expansion_is_deterministic_and_picks_one_option(self) -> None:
        pick = lambda group, options: len(options) - 1
        text, choices = expand_braces("a, {x|y|z}, b, {p|q}", pick)
        self.assertEqual(text, "a, z, b, q")
        self.assertEqual([chosen for _, chosen in choices], ["z", "q"])

    def test_nested_groups_are_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            expand_braces("{a|{b|c}}", lambda group, options: 0)


class PromptTests(unittest.TestCase):
    def _resolve(self, project, positive: str, negative: str = "", **kwargs):
        return resolve_prompt(
            project,
            positive=positive,
            negative=negative,
            section=kwargs.pop("section", "sprite"),
            job_key=kwargs.pop("job_key", "k"),
            trial=kwargs.pop("trial", 1),
            route_tags=kwargs.pop("route_tags", ()),
            loras=kwargs.pop("loras", {}),
            negatives=kwargs.pop("negatives", NegativeSet()),
            width=kwargs.pop("width", 1024),
            height=kwargs.pop("height", 1344),
        )

    def test_negative_always_has_required_words(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = load_project(helpers.make_project(Path(tmp) / "p"))
            resolved = self._resolve(project, "1girl", "low quality", negatives=NegativeSet(always=("watermark",)))
            tags = split_tags(resolved.negative)
            for word in ("low quality", "watermark", "child", "loli", "teen"):
                self.assertIn(word, tags)

    def test_route_tag_added_once_even_with_weight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = load_project(helpers.make_project(Path(tmp) / "p"))
            added = self._resolve(project, "1girl, solo", route_tags=("sex",))
            self.assertIn("sex", split_tags(added.positive))
            kept = self._resolve(project, "1girl, (sex:1.2)", route_tags=("sex",))
            self.assertEqual(split_tags(kept.positive).count("(sex:1.2)"), 1)
            self.assertNotIn("sex", split_tags(kept.positive))

    def test_lora_word_becomes_tag_and_is_not_doubled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = load_project(helpers.make_project(Path(tmp) / "p"))
            loras = {"red hair": LoraEntry("red hair", "red_hair_lora", 0.8)}
            resolved = self._resolve(project, "1girl, red hair", loras=loras)
            tags = split_tags(resolved.positive)
            self.assertIn("<lora:red_hair_lora:0.8>", tags)
            self.assertNotIn("red hair", tags)
            again = self._resolve(project, "1girl, red hair, <lora:red_hair_lora:0.5>", loras=loras)
            self.assertEqual(sum(tag.startswith("<lora:red_hair_lora") for tag in split_tags(again.positive)), 1)

    def test_blocked_word_stops_the_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = load_project(helpers.make_project(Path(tmp) / "p"))
            with self.assertRaises(Exception) as caught:
                self._resolve(project, "1girl, loli")
            self.assertEqual(getattr(caught.exception, "code", ""), "cast_excluded")

    def test_composition_conflict_warns_or_drops(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = load_project(helpers.make_project(Path(tmp) / "p"))
            warned = self._resolve(project, "1girl, landscape composition")
            self.assertTrue(any(note.startswith("composition_conflict") for note in warned.notes))
            self.assertIn("landscape composition", split_tags(warned.positive))
            text = helpers.PROJECT.replace("trials:", "prompt:\n  composition: drop\ntrials:")
            dropping = load_project(helpers.make_project(Path(tmp) / "q", project=text))
            dropped = self._resolve(dropping, "1girl, landscape composition")
            self.assertNotIn("landscape composition", split_tags(dropped.positive))


class PlanTests(unittest.TestCase):
    def test_counts_and_stage_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = _plan(tmp)
            first = [job for job in plan.jobs if job.trial == 1]
            self.assertEqual(len(first), 4)
            chain = next(job for job in first if job.kind is JobKind.CHAIN)
            self.assertEqual(chain.stages, ("dim", "bright", "flare"))
            self.assertEqual([stage for _, stage in chain.scenes], ["dim", "bright", "flare"])
            self.assertIn("glow", split_tags(chain.positive))
            self.assertEqual(len(plan.jobs), 12)

    def test_trial_major_batches_do_not_mix_trials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = _plan(tmp)
            self.assertEqual([batch.batch_id for batch in plan.batches], ["t1-b1", "t2-b1", "t3-b1"])
            jobs = {job.job_id: job for job in plan.jobs}
            for batch in plan.batches:
                self.assertEqual({jobs[j].trial for j in batch.job_ids}, {batch.trial})

    def test_batches_respect_the_job_cap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            text = helpers.PROJECT.replace("max_jobs: 50", "max_jobs: 3")
            plan = _plan(tmp, project=text)
            self.assertEqual([len(batch.job_ids) for batch in plan.batches if batch.trial == 1], [3, 1])

    def test_scene_major_order_groups_trials_per_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            text = helpers.PROJECT.replace("order: trial_major", "order: scene_major")
            plan = _plan(tmp, project=text)
            self.assertEqual([job.trial for job in plan.jobs[:3]], [1, 2, 3])
            self.assertEqual(len({job.key for job in plan.jobs[:3]}), 1)

    def test_character_choice_is_stable_across_runs_and_varies_by_trial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = _plan(tmp)
            second = _plan(tmp + "/again")
            picks = lambda plan: [job.positive for job in plan.jobs if job.key == "S01_standing_01"]
            self.assertEqual(picks(first), picks(second))
            self.assertTrue(all("{" not in positive for positive in picks(first)))

    def test_rotate_policy_gives_three_different_choices(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            text = helpers.PROJECT.replace("trials:", "prompt:\n  char_policy: rotate\ntrials:")
            plan = _plan(tmp, project=text)
            chosen = [job.choices[0][1] for job in plan.jobs if job.key == "S01_standing_01"]
            self.assertEqual(len(set(chosen)), 3)

    def test_face_hint_warning_only_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual([i.code for i in _plan(tmp).warnings if i.code == "face_hint_missing"], [])
            scenes = helpers.SCENES.replace("holding lantern, looking at viewer", "holding lantern")
            plan = _plan(tmp + "/b", scenes=scenes)
            self.assertIn("face_hint_missing", [issue.code for issue in plan.warnings])

    def test_blocked_prompt_is_a_plan_error_not_a_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenes = helpers.SCENES.replace("waving", "waving, child")
            plan = _plan(tmp, scenes=scenes)
            self.assertEqual({issue.code for issue in plan.errors}, {"cast_excluded"})
            self.assertEqual(len([e for e in plan.errors]), 1)

    def test_skip_scenes_removes_solo_scenes_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            text = helpers.PROJECT.replace("trials:", "skip_scenes: [6]\ntrials:")
            plan = _plan(tmp, project=text)
            self.assertEqual(len([j for j in plan.jobs if j.trial == 1]), 3)
            self.assertNotIn("S06_multi_sheet", plan.planned_scene_ids())
            chain_member = helpers.PROJECT.replace("trials:", "skip_scenes: [3]\ntrials:")
            with self.assertRaises(ConfigError):
                _plan(tmp + "/b", project=chain_member)


if __name__ == "__main__":
    unittest.main()
