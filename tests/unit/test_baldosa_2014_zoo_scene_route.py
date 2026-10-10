"""Source 2014 Snes9x scene *must not* be padded by Baldosa press-release."""
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
import baldosa_2014_zoo_calibrated_input as calibration
import baldosa_qa_dense_scene_input_patch as qa_patch


class Baldosa2014ZooSceneTest(unittest.TestCase):
    def test_source_scene_has_no_press_timing_gaps(self):
        upstream = (
            "turbo on\nuntil16 0053 == F60C\nwait 300\n"
            "press start 2\nuntil16 0053 == 8610\n"
            "until 0E1F != 00\npress left 6000\n"
            "until16 0053 == F60C\nwait 300\ndump end\nquit\n"
        )
        prefix = mod.source_menu_prefix(upstream)
        self.assertTrue(prefix.endswith(
            "until16 0053 == 8610\nuntil 0313 == 01\ndump scene-entered\n"))
        cal = mod.render_calibration(prefix)
        route = mod.render_replay(prefix)
        self.assertTrue(cal.endswith("dump scene-entered\nquit\n"))
        self.assertTrue(route.endswith(
            "wait 2979\ndump pre-result\nuntil 009F == BC 1200\n"
            "dump result-onset-candidate\nwait 8\n"
            "dump result-stable-candidate\nquit\n"))
        self.assertEqual([l for l in route.splitlines() if l.startswith("press ")],
                         [l for l in prefix.splitlines() if l.startswith("press ")])
        self.assertNotIn("press left 6000", route)
        boundary = mod.render_fixed_boundary(prefix)
        self.assertNotIn("until 009F == BC", boundary)
        self.assertIn("wait 4700\ndump boundary-04700\n", boundary)
        self.assertIn("wait 1\ndump boundary-05158\n", boundary)
        self.assertIn("dump boundary-05175\nquit\n", boundary)
        self.assertEqual(boundary.count("dump boundary-"), len(mod.BOUNDARY_FRAMES))
        self.assertEqual([l for l in boundary.splitlines() if l.startswith("press ")],
                         [l for l in prefix.splitlines() if l.startswith("press ")])
        for frame in mod.PROGRESS_FRAMES:
            self.assertIn(f"dump progress-{frame:04d}\n", route)
        with self.assertRaises(ValueError):
            mod.source_menu_prefix(upstream.replace("until 0E1F != 00\n", ""))

    def test_phase_calibration_uses_measured_guest_dump_not_input_guess(self):
        self.assertEqual(calibration.guest_scene_entry(
            "script f=1604 dump scene-entered fb=256x224\n"), 1604)
        self.assertEqual(calibration.guest_scene_entry(
            "script f=1606 dump scene-entered ok\n"), 1606)
        for log in ("no entry\n", "script f=8 dump scene-entered ok\n"
                    "script f=9 dump scene-entered ok\n"):
            with self.assertRaises(ValueError):
                calibration.guest_scene_entry(log)

    def test_only_bounded_native_input_phase_changes_guest_origin(self):
        self.assertEqual(calibration.native_input_origin(1606, -1), 1605)
        self.assertEqual(calibration.native_input_origin(1606, 0), 1606)
        self.assertEqual(calibration.native_input_origin(1606, +1), 1607)
        for phase in (-2, 2, 20, 1.0, True):
            with self.assertRaises(ValueError):
                calibration.native_input_origin(1606, phase)
        with self.assertRaises(ValueError):
            calibration.native_input_origin(0, -1)
        sample = {
            "movie_frame_range": [3190, 3193],
            "relative_input_segments": [
                {"start": 0, "duration": 2, "mask": "0x080"},
                {"start": 3, "duration": 1, "mask": "0x010"},
            ],
        }
        from extract_historical_smv_scene_window import shifted_input_file
        original = shifted_input_file(sample, 1604)
        native_late = shifted_input_file(sample, 1607)
        self.assertIn("1604:2:080", original)
        self.assertIn("1607:2:080", native_late)
        self.assertIn("1610:1:010", native_late)
        self.assertEqual(
            [line.split(":")[1:] for line in original.splitlines() if ":" in line
             and not line.startswith("#")],
            [line.split(":")[1:] for line in native_late.splitlines() if ":" in line
             and not line.startswith("#")],
        )

    def test_dense_movie_shim_is_single_patch_at_active_host_frame(self):
        source = (
            "static uint32 TickScript(void) {\nreturn 0;\n}\n"
            "    inputs |= debug_server_get_controller_inputs();\n"
            "    double profile_start = ProfileStart();\n"
        )
        patched = qa_patch.patch(source)
        self.assertIn("UrQaSceneInputAt((uint32)snes_frame_counter)", patched)
        self.assertIn('getenv("UR_QA_SCENE_INPUT_FILE")', patched)
        self.assertIn("inputs = (inputs & ~0x0fffu) | ur_qa_mask;", patched)
        self.assertIn("frame >= g_ur_qa_last", patched)
        with self.assertRaises(ValueError):
            qa_patch.patch(patched)
        with self.assertRaises(ValueError):
            qa_patch.patch(source.replace("TickScript", "Other"))

    def test_real_original_movie_is_not_translated_into_340_press_commands(self):
        self.assertEqual(mod.FIRST + mod.WINDOW - 1, 8359)
        self.assertEqual(mod.RESULT_ONSET, 8353)
        self.assertEqual(len(mod.INPUT_SHA_1810), 64)
        self.assertLess(mod.BEFORE_RESULT, mod.RESULT_ONSET - mod.FIRST)


if __name__ == "__main__":
    unittest.main()
