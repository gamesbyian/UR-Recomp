"""Negative tests for observed, not fabricated, first original idle attract cycle."""
import unittest
from tools.probe_baldosa_modern_title_attract_win32 import (
    verify_original_source_attract, verify_source_driven_preview,
    verify_original_guest_presentations)

OPEN = "UR_BALDOSA_MODERN_ROOT opened=1"
MAIN = "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=main_menu frame=440 menu=d7 race=00 overlay_title=1"
TITLE = "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=attract_title frame=943 menu=84 race=00 overlay_title=1"
DEMO = "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=demo_race frame=1532 menu=00 race=01 overlay_title=1"


class StockIdleAttractWitnessTest(unittest.TestCase):
    def test_valid_stock_source_cycle_and_no_automatic_visible_credit(self):
        self.assertEqual(
            [x["frame"] for x in verify_original_source_attract(
                "\n".join((OPEN, MAIN, TITLE, DEMO)))],
            [440, 943, 1532])

    def test_source_driven_original_preview_requires_real_wake_separation(self):
        steps = (
            OPEN,
            MAIN,
            TITLE,
            "UR_MODERN_TITLE_STOCK_ATTRACT source_revealed=1 frame=943 menu=84 focus=host guest_writes=0",
            DEMO.replace("overlay_title=1", "overlay_title=0"),
            "UR_MODERN_TITLE_STOCK_ATTRACT restored_title=1 frame=1600 guest_writes=0",
            "UR_MODERN_TITLE_STOCK_ATTRACT p1_wake_consumed=1 frame=1600 race=01",
            "UR_MODERN_TITLE_STOCK_ATTRACT stable_title=1 frame=1640 root_unselected=1",
            "UR_MODERN_TITLE_STOCK_ATTRACT separate_confirm=1 frame=1660",
            "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=1674 input_owned=1",
            "UR_MODERN_TITLE_STOCK_ATTRACT reached_root=1 frame=1690 no_stock_route=1",
        )
        good = "\n".join(steps)
        assert len(verify_source_driven_preview(good)) == 3
        for index in range(1, len(steps)):
            bad = "\n".join(x for i, x in enumerate(steps) if i != index)
            with self.subTest(index=index), self.assertRaises(ValueError):
                verify_source_driven_preview(bad)
        with self.assertRaisesRegex(ValueError, "source guest lifecycle"):
            verify_source_driven_preview(
                good.replace("overlay_title=0", "overlay_title=1"))
        with self.assertRaisesRegex(ValueError, "wake"):
            verify_source_driven_preview(good.replace(
                "separate_confirm=1 frame=1660",
                "separate_confirm=1 frame=1640"))

    def test_reject_forged_guest_events(self):
        good = "\n".join((OPEN, MAIN, TITLE, DEMO))
        bad = (
            good.replace(OPEN, ""),
            good.replace(TITLE + "\n", ""),
            good + "\n" + DEMO,
            "\n".join((OPEN, TITLE, MAIN, DEMO)),
            good.replace("frame=943", "frame=944"),
            good.replace("frame=1532", "frame=1531"),
            good.replace("menu=84", "menu=d7"),
            good.replace("race=01", "race=00"),
            good.replace("overlay_title=1", "overlay_title=0"),
        )
        for content in bad:
            with self.subTest(log=content[-95:]):
                with self.assertRaises(ValueError):
                    verify_original_source_attract(content)


if __name__ == "__main__":
    unittest.main()
