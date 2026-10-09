"""Fixed guest-relative Zoo boundary capture distinguishes script polling from guest semantics."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_2014_zoo_boundary_report as boundary
from baldosa_2014_zoo_scene_route import BOUNDARY_FRAMES


def log(entry):
    lines = [f"script f={entry} dump scene-entered ok"]
    lines += [f"script f={entry+frame} dump boundary-{frame:05d} ok"
              for frame in BOUNDARY_FRAMES]
    return "\n".join(lines) + "\n"

class FixedZooBoundaryTest(unittest.TestCase):
    def test_rejects_host_phase_or_missing_frame(self):
        self.assertEqual(boundary.logged_boundary_frames(log(1604))[
            "last_sampled_absolute"], 1604 + BOUNDARY_FRAMES[-1])
        with self.assertRaisesRegex(ValueError, "wrong or absent"):
            boundary.logged_boundary_frames(
                log(1604).replace("boundary-05163 ok", "boundary-05164 ok"))
        with self.assertRaisesRegex(ValueError, "independent guest scene"):
            boundary.logged_boundary_frames(log(1604).replace(
                "dump scene-entered", "dump wrong-label"))

    def test_equal_fixed_onset_but_post_result_contact_can_differ(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for label in ("original", "native"):
                folder = root / label
                folder.mkdir()
                for frame in BOUNDARY_FRAMES:
                    w = bytearray(0x20000)
                    w[0x00CE] = 1
                    w[0x0313] = 1 if frame < 5163 else 0x3D
                    w[0x009F] = 0 if frame < 5163 else 0xBC
                    if frame >= 5163 and label == "native" and frame >= 5171:
                        w[0x0E95:0x0E97] = (10240).to_bytes(2, "little")
                    (folder / f"boundary-{frame:05d}.wram.bin").write_bytes(w)
            with patch.object(boundary, "Dump", lambda folder, tag: (folder, tag)):
                with patch.object(boundary, "screen_texts",
                                  lambda dumped: ["MIKE", "1:16.46", "LAPS ON ZOOM ZOO"]):
                    result = boundary.analyze(root / "original", root / "native",
                                              log(1604), log(1606))
            self.assertEqual(result["first_fixed_frame_result_menu"],
                             {"original": 5163, "native": 5163})
            self.assertTrue(result["same_fixed_frame_result_onset"])
            self.assertTrue(result["final_ppu_equal"])
            self.assertEqual(result["first_named_field_disagreement"]["relative_frame"],
                             5171)
            self.assertEqual(result["first_named_field_disagreement"]["field"],
                             "p1_stored_contact")
            self.assertEqual(result["complete_event_qa_credit"], 0)

    def test_actual_fixed_menu_mismatch_must_not_be_normalized(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for label in ("original", "native"):
                folder = root / label
                folder.mkdir()
                for frame in BOUNDARY_FRAMES:
                    onset = 5163 if label == "original" else 5162
                    w = bytearray(0x20000)
                    w[0x00CE] = 1
                    w[0x0313] = 1 if frame < onset else 0x3D
                    w[0x009F] = 0 if frame < onset else 0xBC
                    (folder / f"boundary-{frame:05d}.wram.bin").write_bytes(w)
            with patch.object(boundary, "Dump", lambda folder, tag: (folder, tag)):
                with patch.object(boundary, "screen_texts",
                                  lambda dumped: ["MIKE", "1:16.46"]):
                    result = boundary.analyze(root / "original", root / "native",
                                              log(1604), log(1606))
            self.assertEqual(result["first_fixed_frame_result_menu"],
                             {"original": 5163, "native": 5162})
            self.assertFalse(result["same_fixed_frame_result_onset"])
            self.assertEqual(result["first_named_field_disagreement"]["relative_frame"],
                             5162)
            self.assertEqual(result["complete_event_qa_credit"], 0)


if __name__ == "__main__":
    unittest.main()
