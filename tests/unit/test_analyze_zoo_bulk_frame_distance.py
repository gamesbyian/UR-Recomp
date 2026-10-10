"""Full WRAM/VRAM/CGRAM Zoo time-neighbor diagnostic is not course acceptance."""
import io
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import analyze_zoo_bulk_frame_distance as fit


class BulkGuestDistanceTest(unittest.TestCase):
    def make_artifact(self, *, corrupt=False, missing_native=False):
        stream = io.BytesIO()
        zero = {k: bytes(n) for k, n in fit.FIELDS.items()}
        prep = {k: bytearray(n) for k, n in fit.FIELDS.items()}
        prep["wram"][0x9F] = 0x84
        restored = {k: bytearray(n) for k, n in fit.FIELDS.items()}
        restored["wram"][0x9F] = 0x16
        restored["wram"][0xCE] = 1
        with ZipFile(stream, "w", ZIP_DEFLATED) as z:
            for frame, fields in ((5155, zero), (5156, prep), (5157, restored)):
                for k, data in fields.items():
                    z.writestr(f"original-boundary/boundary-{frame:05d}.{k}.bin", data)
            if not missing_native:
                for k, data in restored.items():
                    z.writestr(f"native-boundary/dump/boundary-05156.{k}.bin",
                               data[:-1] if corrupt and k == "wram" else data)
        stream.seek(0)
        return stream

    def test_paired_exact_adjacent_memory_is_observation_not_instruction_time(self):
        with ZipFile(self.make_artifact()) as archive:
            report = fit.compare(archive, 5156, 5156, 1)
        self.assertEqual(report["rows"][0]["native_relative_frame"], 5156)
        best = report["rows"][0]["nearest_original_candidate"]
        self.assertEqual(best["original_relative_frame"], 5157)
        self.assertEqual(best["bytes_different"],
                         {"wram": 0, "vram": 0, "cgram": 0})
        self.assertEqual(report["rows"][0]["same_relative_frame"][
                         "bytes_different"]["wram"], 2)
        self.assertEqual(report["admission"]["release_usa_complete_courses_credited"], 0)
        self.assertEqual(report["admission"]["causal_claim"], "none")

    def test_missing_or_corrupt_guest_dump_rejected(self):
        with ZipFile(self.make_artifact(corrupt=True)) as archive:
            with self.assertRaisesRegex(ValueError, "expected"):
                fit.compare(archive, 5156, 5156, 1)
        with ZipFile(self.make_artifact(missing_native=True)) as archive:
            with self.assertRaisesRegex(ValueError, "native missing"):
                fit.compare(archive, 5156, 5156, 1)
        with self.assertRaisesRegex(ValueError, "only original"):
            fit.compare(None, 5154, 5155)
        with self.assertRaisesRegex(ValueError, "only original"):
            fit.compare(None, 5155, 5156, 4)


if __name__ == "__main__":
    unittest.main()
