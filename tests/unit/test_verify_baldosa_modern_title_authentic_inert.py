"""ROM-free adversarial checks for exact native Authentic title isolation."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from verify_baldosa_modern_title_authentic_inert import (
    check_inert, source_wram_crcs, authentic_presents,
)


def state(crc=None, frames=None, log="original guest only"):
    return {"crc": crc or ["0xA091EF13"] * 180,
            "frames": frames or {16: b"x", 32: b"y", 48: b"z"},
            "log": log}


class TitleAuthenticInertTests(unittest.TestCase):
    def test_identical_real_source_evidence_is_admitted(self):
        evidence = check_inert(state(), state())
        self.assertEqual(evidence["original_frames"], 180)
        self.assertEqual(evidence["common_present_frames"], [16, 32, 48])
        self.assertTrue(evidence["identical_host_presented_pixels"])
        self.assertFalse(evidence["modern_title_or_root_present"])
        self.assertEqual(evidence["authentic_output_raster"], "256x224")

    def test_title_root_logging_fails_closed(self):
        for marker in ("UR_BALDOSA_MODERN_TITLE painted=1",
                       "UR_BALDOSA_MODERN_ROOT opened=1"):
            with self.subTest(marker=marker):
                with self.assertRaisesRegex(ValueError, "activated inside Authentic"):
                    check_inert(state(), state(log=marker))

    def test_source_timeline_mismatch_rejected(self):
        alternate = state(crc=["0xE0FFFFFF"] * 180)
        with self.assertRaisesRegex(ValueError, "WRAM CRC timeline"):
            check_inert(state(), alternate)

    def test_host_present_mismatch_and_inadequate_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError, "displayed pixels"):
            check_inert(state(), state(frames={
                16: b"x", 32: b"DIFFERENT", 48: b"z"}))
        with self.assertRaisesRegex(ValueError, "Fewer than three common"):
            check_inert(state(), state(frames={16: b"x", 200: b"y"}))

    def test_missing_or_reordered_original_frame_files_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            with self.assertRaisesRegex(ValueError, "fewer than 100"):
                source_wram_crcs(folder)
            for i in range(100):
                (folder / f"frame_{i:06d}.json").write_text(
                    '{"frame": 0, "crc32_wram": "0xA091EF13"}')
            self.assertEqual(len(source_wram_crcs(folder)), 100)
            (folder / "frame_000099.json").rename(
                folder / "frame_000111.json")
            with self.assertRaisesRegex(ValueError, "missing/duplicate"):
                source_wram_crcs(folder)

    def test_actual_present_frames_reject_missing_or_wrong_schema(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            with self.assertRaisesRegex(ValueError, "no presentation CSV"):
                authentic_presents(folder)
            (folder / "presents.csv").write_text(
                "present,frame,alpha,crc32\n0,16,0,12345678\n")
            with self.assertRaisesRegex(ValueError, "schema drift"):
                authentic_presents(folder)

    def test_windows_runner_hooks_remain_mode_gated(self):
        source = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text()
        adapter = (ROOT / "tools/baldosa_modern_profile_activation_spike.py").read_text()
        workflow = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertIn('std::strcmp(mode, "authentic") == 0', source)
        self.assertIn("if (!configured()) return;", source)
        self.assertIn("return configured() ? 428 : 320;", source)
        self.assertIn("if (!logical_width || !logical_height || !configured() || !g_visible)", source)
        self.assertIn(".prepare_frame       = &ur_baldosa_modern_root_prepare_frame", adapter)
        self.assertIn("verify_baldosa_modern_title_authentic_inert.py", workflow)


if __name__ == "__main__":
    unittest.main()
