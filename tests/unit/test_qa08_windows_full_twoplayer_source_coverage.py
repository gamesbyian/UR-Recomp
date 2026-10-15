"""Original-size source-only 2P split/race/terminal Windows observer gates."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_windows_full_twoplayer_source_coverage as two


class TwoPlayerSourceTest(unittest.TestCase):
    def test_exact_real_source_window_and_terminal_scene_coverage(self):
        self.assertEqual((two.FIRST,two.LAST,two.STEP),(1280,5472,16))
        self.assertEqual(len(range(1280,5473,16)),263)
        self.assertEqual(len([f for f in range(1280,5473,16) if f>=5136]),22)

    def test_fake_or_truncated_native_guest_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            with self.assertRaises(ValueError):
                two.inspect(folder,"",["0x00000000"]*5484)
            log=("UR_QA08_WINDOWS_ORIGINAL_SOURCE frame=1280 "
                 "logical=256x224 saved=1 "
                 "source=post-original-ppu-before-present\n")
            with self.assertRaisesRegex(ValueError,"missing"):
                two.inspect(folder,log,["0x00000000"]*5484)
            with self.assertRaisesRegex(ValueError,"never reached"):
                two.inspect(folder,log,["0x00000000"]*100)

    def test_read_only_two_pad_observer_retains_prior_frozen_controls(self):
        cpp=(ROOT/"tools/baldosa_qa08_windows_original_capture.cpp").read_text()
        self.assertIn('std::strcmp(mode, "twoplayer-fullroute") == 0',cpp)
        self.assertIn('std::strcmp(mode, "oneplayer-coverage") == 0',cpp)
        self.assertIn("kTwoPlayerLast = 5472",cpp)
        self.assertIn("kOnePlayerLast = 5440",cpp)
        self.assertIn("g_seen_default[4]",cpp)
        self.assertIn("g_seen_twoplayer[kTwoPlayerSlots]",cpp)
        self.assertIn("source=post-original-ppu-before-present",cpp)
        self.assertNotIn("ppu_render_pixel(",cpp)

    def test_ci_wires_2p_qa_only_once_after_1p_in_same_windows_title(self):
        workflow=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        entry="python tools/qa08_windows_full_twoplayer_source_coverage.py"
        self.assertEqual(workflow.count(entry),1)
        self.assertLess(workflow.index(
            "python tools/qa08_windows_full_oneplayer_source_coverage.py"),
            workflow.index(entry))
        self.assertEqual(workflow.count(
            "python tests/unit/test_qa08_windows_full_twoplayer_source_coverage.py"),1)


if __name__=="__main__":
    unittest.main()
