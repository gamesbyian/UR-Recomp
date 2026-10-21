"""Adversarial ROM-free controls for a source-emission-only OBJ depth analyzer."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import analyze_baldosa_wide_obj_depth as depth


class ObjDepthEvidenceTests(unittest.TestCase):
    @staticmethod
    def raster(front_visible=True):
        size = depth.WIDTH * depth.HEIGHT * 4
        main = bytearray(size)
        slots = {s: bytearray(size) for s in depth.SOURCE_SLOTS}
        front_rgb = bytes([10, 20, 30])
        back_rgb = bytes([40, 50, 60])
        for y, front, back in ((20, 98, 99), (132, 96, 97)):
            for x in range(40):
                i = (y * depth.WIDTH + x) * 4
                # Original RGBX high byte intentionally remains zero.
                main[i:i+3] = front_rgb if front_visible else back_rgb
                slots[front][i:i+4] = front_rgb + bytes([255])
                slots[back][i:i+4] = back_rgb + bytes([255])
        return bytes(main), {k: bytes(v) for k, v in slots.items()}

    def test_front_emission_witness_with_original_rgbx_alpha_zero(self):
        original, slots = self.raster()
        report = depth.analyze(original, slots, frame=1856, minimum_overlap=32)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["guest_frame"], 1856)
        self.assertEqual(report["stock_alpha_nonzero"], 0)
        for viewport in ("top", "bottom"):
            pair = report[viewport]
            self.assertTrue(pair["source_emission_priority_witness"])
            self.assertEqual(pair["source_overlap_pixels"], 40)
            self.assertEqual(pair["overlap_front_rgb_matches_original"], 40)
            self.assertEqual(pair["overlap_rear_rgb_matches_original"], 0)
            self.assertEqual(pair["pixels_outside_slot_viewport"], 0)

    def test_matching_rear_source_is_not_front_priority_witness(self):
        original, slots = self.raster(front_visible=False)
        report = depth.analyze(original, slots, frame=1856, minimum_overlap=32)
        self.assertEqual(report["status"], "unproven")
        for viewport in ("top", "bottom"):
            self.assertFalse(report[viewport]["source_emission_priority_witness"])
            self.assertEqual(report[viewport]["overlap_rear_rgb_matches_original"], 40)

    def test_zero_overlap_and_boolean_thresholds_fail_closed(self):
        size = depth.WIDTH * depth.HEIGHT * 4
        original = bytes(size)
        slots = {s: bytes(size) for s in depth.SOURCE_SLOTS}
        for frame, threshold in ((1856, 0), (1856, True), (True, 32),
                                 (-1, 32), (1856, -1), (1856, 1.0)):
            with self.subTest(frame=frame, threshold=threshold), self.assertRaises(ValueError):
                depth.analyze(original, slots, frame=frame, minimum_overlap=threshold)

    def test_missing_slot_bad_raster_and_wrong_pam_header_refused(self):
        original, slots = self.raster()
        with self.assertRaises(ValueError):
            depth.analyze(original, {96: slots[96]}, 1856, 32)
        with self.assertRaises(ValueError):
            depth.analyze(original[:-1], slots, 1856, 32)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.pam"
            path.write_bytes(depth.HEADER + original)
            self.assertEqual(depth.read_native_pam(path), original)
            path.write_bytes(b"P7\n" + original)
            with self.assertRaises(ValueError):
                depth.read_native_pam(path)

    def test_existing_report_never_overwritten(self):
        original, slots = self.raster()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "original"
            slot_dir = root / "slots"
            source.mkdir()
            slot_dir.mkdir()
            frame = 1856
            (source / f"ur-baldosa-ws342-{frame:06d}.pam").write_bytes(depth.HEADER + original)
            for slot, payload in slots.items():
                (slot_dir / f"ur-baldosa-ws342-obj-slot{slot}-frame{frame:06d}.pam").write_bytes(
                    depth.HEADER + payload)
            existing = root / "report.json"
            existing.write_text("immutable")
            with patch.object(sys, "argv", ["analyzer", "--original-dir", str(source),
                    "--slot-dir", str(slot_dir), "--frame", str(frame), "--out", str(existing)]):
                with self.assertRaises(FileExistsError):
                    depth.main()
            self.assertEqual(existing.read_text(), "immutable")


if __name__ == "__main__":
    unittest.main()
