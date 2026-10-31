"""The H3 window names one lane and does not generate."""

from __future__ import annotations

import contextlib
import io
import unittest

from h3.desk import LANES, DeskError, choose, main, render


class DeskTests(unittest.TestCase):
    def test_every_lane_has_the_same_fields(self) -> None:
        for item in LANES.values():
            for text in (
                item.title,
                item.effect,
                item.give,
                item.when,
                item.story,
                item.prompt,
                item.quality,
                item.speed,
                item.loras,
                item.code,
            ):
                self.assertTrue(text.strip(), item.id)
            self.assertNotIn("生成する", item.speed + item.quality)
            self.assertNotIn("Hana", item.effect + item.title)

    def test_only_live_remake_is_in_this_checkout(self) -> None:
        present = [item.id for item in LANES.values() if item.present]
        self.assertEqual(present, ["live_remake", "reproduce"])

    def test_choose_is_one_lane_or_a_stop(self) -> None:
        self.assertEqual(choose("元動画を静止画に合わせる live_remake"), "live_remake")
        self.assertEqual(choose("格闘"), "combat_motion")
        self.assertEqual(choose("百裂"), "affi_chain")
        with self.assertRaises(DeskError):
            choose("")
        with self.assertRaises(DeskError):
            choose("今日の天気")
        with self.assertRaises(DeskError):
            choose("live_remake と 格闘")
        with self.assertRaises(DeskError):
            choose("元動画を完全再現")
        self.assertEqual(choose("完全再現"), "reproduce")

    def test_cards_say_generation_stays_off(self) -> None:
        text = render()
        self.assertIn("[live_remake] このcheckout", text)
        self.assertIn("機能: 元動画の顔と衣装を、渡した静止画に合わせる", text)
        self.assertIn("入れると:", text)
        self.assertIn("生成: しない", text)
        self.assertNotIn("Hana", text)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--generate"]), 1)
            self.assertEqual(main(["combat_motion"]), 0)
            self.assertEqual(main(["reproduce"]), 2)


if __name__ == "__main__":
    unittest.main()
