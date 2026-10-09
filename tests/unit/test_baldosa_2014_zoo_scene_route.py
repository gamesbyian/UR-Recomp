"""2014 original Zoo controller masks to Baldosa route, never result credit."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location(
    "zoo_scene", ROOT / "tools/baldosa_2014_zoo_scene_route.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class Baldosa2014ZooSceneTest(unittest.TestCase):
    def test_source_masks_preserve_duration_order_and_idle_frames(self):
        commands = mod.scene_commands([
            {"start": 0, "duration": 3, "mask": "0x041"},
            {"start": 5, "duration": 4, "mask": "0x281"},
            {"start": 9, "duration": 1, "mask": "0x008"},
        ], count=14)
        self.assertEqual(commands, [
            "press b+left 3", "wait 2", "press b+right+x 4",
            "press start 1", "wait 4"
        ])

    def test_original_menu_source_is_guarded(self):
        good = (
            "turbo on\nuntil16 0053 == F60C\nwait 300\n"
            "press start 2\nuntil16 0053 == 8610\n"
            "until 0E1F != 00\npress left 6000\n"
            "until16 0053 == F60C\nwait 300\ndump end\nquit\n"
        )
        prefix = mod.source_menu_prefix(good)
        self.assertTrue(prefix.endswith(
            "until16 0053 == 8610\nuntil 0313 == 01\ndump scene-entered\n"))
        route = mod.render(prefix, [{"start": 0, "duration": 1, "mask": "0x040"}], 3)
        self.assertIn("press left 1\nwait 2\ndump result-onset-candidate", route)
        self.assertTrue(route.endswith(
            "dump result-onset-candidate\nwait 6\n"
            "dump result-stable-candidate\nquit\n"))
        self.assertNotIn("press left 6000", route)
        with self.assertRaises(ValueError):
            mod.source_menu_prefix(good.replace("until 0E1F != 00\n", ""))
        with self.assertRaises(ValueError):
            mod.source_menu_prefix(good.replace("press left 6000", "press left 5"))

    def test_bad_masks_overlaps_and_gaps_fail_closed(self):
        for rows, count in (
            ([{"start": 0, "duration": 2, "mask": "0x000"}], 5),
            ([{"start": 0, "duration": 6, "mask": "0x040"}], 5),
            ([{"start": 0, "duration": 2, "mask": "0x040"},
              {"start": 1, "duration": 1, "mask": "0x080"}], 5),
            ([{"start": 0, "duration": 1, "mask": "0x1000"}], 5),
        ):
            with self.subTest(rows=rows):
                with self.assertRaises(ValueError):
                    mod.scene_commands(rows, count)

    def test_source_scene_horizon_is_movie_result_not_route_completion(self):
        self.assertEqual(mod.FIRST + mod.WINDOW - 1, 8359)
        self.assertEqual(mod.RESULT_ONSET, 8353)
        self.assertEqual(len(mod.INPUT_SHA_1810), 64)


if __name__ == "__main__":
    unittest.main()
