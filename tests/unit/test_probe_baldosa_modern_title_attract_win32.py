"""Negative tests for observed, not fabricated, first original idle attract cycle."""
import unittest
from tools.probe_baldosa_modern_title_attract_win32 import verify_original_source_attract

OPEN = "UR_BALDOSA_MODERN_ROOT opened=1"
MAIN = "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=main_menu frame=440 menu=d7 race=00 overlay_title=1"
TITLE = "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=attract_title frame=943 menu=84 race=00 overlay_title=1"
DEMO = "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=demo_race frame=1531 menu=3d race=01 overlay_title=1"


class StockIdleAttractWitnessTest(unittest.TestCase):
    def test_valid_stock_source_cycle_and_no_automatic_visible_credit(self):
        self.assertEqual(
            [x["frame"] for x in verify_original_source_attract(
                "\n".join((OPEN, MAIN, TITLE, DEMO)))],
            [440, 943, 1531])

    def test_reject_forged_guest_events(self):
        good = "\n".join((OPEN, MAIN, TITLE, DEMO))
        bad = (
            good.replace(OPEN, ""),
            good.replace(TITLE + "\n", ""),
            good + "\n" + DEMO,
            "\n".join((OPEN, TITLE, MAIN, DEMO)),
            good.replace("frame=943", "frame=944"),
            good.replace("frame=1531", "frame=1532"),
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
