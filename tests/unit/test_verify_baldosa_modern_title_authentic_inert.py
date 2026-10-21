"""ROM-free adversarial checks for exact native Authentic title isolation."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from verify_baldosa_modern_title_authentic_inert import (
    check_inert, source_wram_crcs, authentic_presents,
    authentic_ink_visible, retain_authentic_visible_frame,
)


# Source-format fixtures test *admission logic only*, never stand in for
# a ROM/real-host screenshot or release claim.
INK = bytes((i % 5 * 43 + 1 for pixel in range(256 * 224)
             for i in (pixel, pixel + 1, pixel + 2)))
BLACK = bytes(256 * 224 * 3)


def state(crc=None, frames=None, log="original guest only"):
    return {"crc": crc or ["0xA091EF13"] * 320,
            "frames": frames if frames is not None else
                      {16: BLACK, 240: INK, 256: INK},
            "log": log}


class TitleAuthenticInertTests(unittest.TestCase):
    def test_identical_real_source_evidence_is_admitted(self):
        evidence = check_inert(state(), state())
        self.assertEqual(evidence["original_frames"], 320)
        self.assertEqual(evidence["common_present_frames"], [16, 240, 256])
        self.assertEqual(evidence["visible_original_guest_present_frames"], [240, 256])
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
        alternate = state(crc=["0xE0FFFFFF"] * 320)
        with self.assertRaisesRegex(ValueError, "WRAM CRC timeline"):
            check_inert(state(), alternate)

    def test_host_present_mismatch_and_inadequate_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError, "displayed pixels"):
            check_inert(state(), state(frames={
                16: BLACK, 240: b"DIFFERENT", 256: INK}))
        with self.assertRaisesRegex(ValueError, "Fewer than three common"):
            check_inert(state(), state(frames={16: BLACK, 200: INK}))

    def test_identical_black_or_uniform_guest_is_not_visual_isolation_proof(self):
        self.assertFalse(authentic_ink_visible(BLACK))
        self.assertTrue(authentic_ink_visible(INK))
        self.assertFalse(authentic_ink_visible(bytes((30, 40, 60)) * (256 * 224)))
        blank = state(frames={16: BLACK, 240: BLACK, 256: BLACK})
        with self.assertRaisesRegex(ValueError, "blank/uniform"):
            check_inert(blank, blank)
        early = state(frames={16: INK, 32: INK, 48: INK})
        with self.assertRaisesRegex(ValueError, "blank/uniform"):
            check_inert(early, early)
        incomplete = state(frames={16: BLACK, 240: b"INVALID", 256: BLACK})
        with self.assertRaisesRegex(ValueError, "blank/uniform"):
            check_inert(incomplete, incomplete)

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

    def test_exact_late_original_ppm_bytes_retained_only_once(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = root / "authentic-root-disabled"
            screenshots = original / "presented"
            screenshots.mkdir(parents=True)
            (screenshots / "presents.csv").write_text(
                "present,frame,alpha,crc32,luma\n"
                "0,320,0,00112233,100\n")
            source_bytes = b"P6\n256 224\n255\n" + INK
            (screenshots / "present_000000.ppm").write_bytes(source_bytes)
            record = retain_authentic_visible_frame(
                original, root, 320, "disabled")
            retained = root / record["file"]
            self.assertEqual(retained.read_bytes(), source_bytes)
            self.assertEqual(record["sha256"],
                             hashlib.sha256(source_bytes).hexdigest())
            self.assertEqual(record["origin"],
                             "actual_baldosa_post_osd_before_sdl_upload")
            with self.assertRaisesRegex(ValueError, "already exists"):
                retain_authentic_visible_frame(original, root, 320, "disabled")
            retained.unlink()
            (screenshots / "present_000000.ppm").write_bytes(
                b"P6\n256 224\n255\n" + BLACK)
            with self.assertRaisesRegex(ValueError, "uniform/blank"):
                retain_authentic_visible_frame(original, root, 320, "disabled")
            with self.assertRaisesRegex(ValueError, "missing or duplicated"):
                retain_authentic_visible_frame(original, root, 319, "disabled")

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
