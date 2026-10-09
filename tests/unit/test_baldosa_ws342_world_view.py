"""Accept a bounded 342x224 source-world raster, not just the 304-wide bridge."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "baldosa_world_report", ROOT / "tools/baldosa_ws24_presentation_report.py")
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)

FULL_HEADER = (b"P7\nWIDTH 342\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
               b"TUPLTYPE RGB_ALPHA\nENDHDR\n")


class BaldosaWide342Tests(unittest.TestCase):
    def test_genuine_43_pixel_margins_in_both_views(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, candidate, log = (root / name for name in ("base", "candidate", "log"))
            seq = ("0xABCDEF42\n" * 2473).encode()
            base.write_bytes(seq)
            candidate.write_bytes(seq)
            log.write_text("".join(
                f"UR_BALDOSA_WS342_PREP frame={frame} calibrated=1 "
                f"logical=342x224 backing=48 visible=43\n"
                f"UR_BALDOSA_WS342_PRESENT frame={frame} width=342 height=224 "
                f"pitch=1368 calibrated=1 saved=1\n"
                for frame in (1808, 1856)))
            folder = root / "captures"
            folder.mkdir()
            for frame, shade in ((1808, 15), (1856, 40)):
                pixels = bytearray(342 * 224 * 4)
                for y in range(224):
                    for x in list(range(43)) + list(range(299, 342)):
                        offset = (y * 342 + x) * 4
                        pixels[offset:offset + 4] = bytes((shade, 80, 100, 255))
                (folder / f"ur-baldosa-ws342-{frame:06d}.pam").write_bytes(
                    FULL_HEADER + pixels)
            result = report.assess(base, candidate, log, folder, view="ws342")
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["host_wide_raster"], [342, 224])
            self.assertEqual(result["backing_course_margin"], 48)
            self.assertEqual(result["per_side_new_world_pixels"], 43)
            log.write_text(log.read_text().replace("backing=48", "backing=24"))
            self.assertEqual(report.assess(base, candidate, log, folder, view="ws342")["status"], "unproven")
            log.write_text(log.read_text().replace("backing=24", "backing=48"))
            (folder / "ur-baldosa-ws342-001856.pam").write_bytes(
                FULL_HEADER + bytes(342 * 224 * 4))
            self.assertEqual(report.assess(base, candidate, log, folder, view="ws342")["status"], "unproven")
            with self.assertRaises(ValueError):
                report.assess(base, candidate, log, folder, view="arbitrary")


if __name__ == "__main__":
    unittest.main()
