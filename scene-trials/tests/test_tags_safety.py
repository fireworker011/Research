from __future__ import annotations

import unittest

import helpers
from scene_trials.errors import SafetyError
from scene_trials.safety import (
    REQUIRED_NEGATIVES,
    ensure_required_negatives,
    find_blocked,
    require_adult_confirmation,
)
from scene_trials.tags import dedupe_tags, has_tag, split_tags, tag_key


def setUpModule() -> None:
    assert helpers.SCENES  # importing helpers puts src on sys.path


class TagTests(unittest.TestCase):
    def test_split_keeps_brackets_whole(self) -> None:
        text = "a, (b, c:1.2), <lora:x:0.8>, {p|q}, d"
        self.assertEqual(split_tags(text), ["a", "(b, c:1.2)", "<lora:x:0.8>", "{p|q}", "d"])

    def test_key_strips_weight_and_case(self) -> None:
        self.assertEqual(tag_key("(Looking  Back:1.3)"), "looking back")
        self.assertTrue(has_tag(["(sex:1.2)"], "sex"))

    def test_dedupe_keeps_first_spelling(self) -> None:
        self.assertEqual(dedupe_tags(["A", "(a:1.1)", "b"]), ["A", "b"])


class SafetyTests(unittest.TestCase):
    def test_required_negatives_cannot_be_dropped(self) -> None:
        merged = ensure_required_negatives(["low quality"])
        for word in REQUIRED_NEGATIVES:
            self.assertIn(word, merged)

    def test_whole_word_matching(self) -> None:
        self.assertEqual(find_blocked("1girl, lolita dress"), "lolita")
        self.assertEqual(find_blocked("1girl, child"), "child")
        self.assertIsNone(find_blocked("glorious light, childhood friend"))
        self.assertEqual(find_blocked("小学生, 1girl"), "小学生")
        self.assertEqual(find_blocked("1girl, custom", ("custom",)), "custom")

    def test_adult_confirmation_needs_both_fields(self) -> None:
        with self.assertRaises(SafetyError):
            require_adult_confirmation("", "2026-11-15")
        with self.assertRaises(SafetyError):
            require_adult_confirmation("owner", "")
        require_adult_confirmation("owner", "2026-11-15")


if __name__ == "__main__":
    unittest.main()
