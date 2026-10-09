"""Production native per-slot alpha witness must preserve the Original field."""
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_wide_single_slot_source import (
    HEADER, WIDTH, HEIGHT, assess, read_source
)


def fixture_source(slot: int, frame: int, top=True, bottom=True):
    data = bytearray(WIDTH * HEIGHT * 4)
    positions = []
    if top:
        positions.append((11, 40))
    if bottom:
        positions.append((331, 130))
    for x, y in positions:
        offset = (y * WIDTH + x) * 4
        data[offset:offset + 4] = bytes((10, 20, 30, 255))
    name = f"ur-baldosa-ws342-obj-slot{slot}-frame{frame:06d}.pam"
    return name, bytes(data)


class BaldosaWideSourceSlotTest(unittest.TestCase):
    def test_source_metadata_and_no_original_ppu_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            name, data = fixture_source(98, 1856)
            path = root / name
            path.write_bytes(HEADER + data)
            source = read_source(path, 98)
            self.assertTrue(source["source_nonempty"])
            self.assertEqual(source["bbox"], [11, 40, 331, 130])
            self.assertEqual(source["top_opaque_source_pixels"], 1)
            self.assertEqual(source["bottom_opaque_source_pixels"], 1)
            base = {
                1808: b"a" * 100,
                1856: b"b" * 100,
                1888: b"c" * 100,
            }
            log = (
                "UR_RACER_HD_WIDE_SOURCE frame=1856 slot=98 status=source "
                "top_alpha=1 bottom_alpha=1 bbox=11,40,331,130 "
                f"path=/repo/captures/{name}\n"
            )
            proof = assess(base, dict(base), source, log,
                           min_shared_frames=2)
            self.assertEqual(proof["status"], "passed")
            self.assertEqual(proof["identical_complete_original_342_rasters"], 3)
            self.assertTrue(proof["source_log_matches_pam"])
            # An isolated slot must not alter even a single stock main pixel.
            modified = {**base, 1856: b"X" + b"b" * 99}
            self.assertEqual(assess(base, modified, source, log,
                                    min_shared_frames=2)["status"], "unproven")
            # A plausible report that lies about per-slot alpha is rejected.
            false_log = log.replace("bottom_alpha=1", "bottom_alpha=0")
            self.assertFalse(assess(base, dict(base), source, false_log,
                                    min_shared_frames=2)["source_log_matches_pam"])
            # A second source log for the same slot and frame is ambiguous.
            self.assertEqual(assess(base, dict(base), source, log + log,
                                    min_shared_frames=2)["status"], "unproven")
            with self.assertRaisesRegex(ValueError, "Incorrect source"):
                read_source(path, 99)
            path.write_bytes(HEADER + data[:-1])
            with self.assertRaisesRegex(ValueError, "Malformed"):
                read_source(path, 98)

    def test_empty_slot_is_valid_source_absence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            name, data = fixture_source(96, 1856, top=False, bottom=False)
            path = root / name
            path.write_bytes(HEADER + data)
            source = read_source(path, 96)
            self.assertFalse(source["source_nonempty"])
            self.assertEqual(source["bbox"], [WIDTH, HEIGHT, -1, -1])
            log = (
                "UR_RACER_HD_WIDE_SOURCE frame=1856 slot=96 status=empty "
                "top_alpha=0 bottom_alpha=0 bbox=342,224,-1,-1 "
                f"path=/repo/captures/{name}\n"
            )
            main = {1808: b"0", 1856: b"1", 1888: b"2"}
            proof = assess(main, dict(main), source, log, min_shared_frames=2)
            self.assertEqual(proof["status"], "passed")
            self.assertFalse(proof["source"]["source_nonempty"])


if __name__ == "__main__":
    unittest.main()
