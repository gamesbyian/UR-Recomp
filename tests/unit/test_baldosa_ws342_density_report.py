"""A 342x224 world image at 4x must contain 1368x896 real pixels.

Tests detect one-subpixel corruption and stale 1x logs; source image detail
in *both* split margins and identical guest CRC alone are not sufficient.
"""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "baldosa_wide_density", ROOT / "tools/baldosa_ws24_presentation_report.py")
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def native_rgba_4x(shade):
    width, height, scale = 342, 224, 4
    logical = bytearray(width * height * 4)
    for y in range(height):
        for x in list(range(43)) + list(range(299, width)):
            at = (y * width + x) * 4
            logical[at:at + 4] = bytes((shade, y & 255, x & 255, 255))
    out = bytearray()
    for y in range(height):
        row = logical[y * width * 4:(y + 1) * width * 4]
        physical_row = b"".join(
            row[x * 4:x * 4 + 4] * scale for x in range(width))
        for _ in range(scale):
            out.extend(physical_row)
    return bytes(out)


class BaldosaWideDensityEvidenceTest(unittest.TestCase):
    def test_exact_4x_world_and_corrupt_subpixel(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, candidate, log = (root / p for p in ("base", "candidate", "log"))
            crc = ("deadbeef\n" * 2473).encode()
            base.write_bytes(crc)
            candidate.write_bytes(crc)
            log.write_text("".join(
                f"UR_BALDOSA_WS342_PREP frame={f} calibrated=1 "
                f"logical=342x224 backing=48 visible=43\n"
                f"UR_BALDOSA_WS342_PRESENT frame={f} width=342 height=224 "
                f"pitch=5472 calibrated=1 saved=1 "
                f"density=4 raster=1368x896\n"
                for f in (1808, 1856)))
            folder = root / "captures"
            folder.mkdir()
            header = (b"P7\nWIDTH 1368\nHEIGHT 896\nDEPTH 4\n"
                      b"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n")
            files = []
            for frame, shade in ((1808, 15), (1856, 40)):
                path = folder / f"ur-baldosa-ws342-{frame:06d}.pam"
                path.write_bytes(header + native_rgba_4x(shade))
                files.append(path)

            accepted = report.assess(base, candidate, log, folder,
                                     view="ws342", density=4)
            self.assertEqual(accepted["status"], "passed")
            self.assertEqual(accepted["presentation_raster"], [1368, 896])
            self.assertTrue(all(f["exact_nearest_blocks"] for f in accepted["captures"]))
            # A single wrong pixel, even inside the authored world margin,
            # disqualifies the complete 4x frame.
            corrupt = bytearray(files[1].read_bytes())
            corrupt[len(header) + 4] ^= 1
            files[1].write_bytes(corrupt)
            refused = report.assess(base, candidate, log, folder,
                                    view="ws342", density=4)
            self.assertEqual(refused["status"], "unproven")
            self.assertFalse(refused["captures"][1]["exact_nearest_blocks"])
            # No 1x log record can be used to claim a 4x native allocation.
            log.write_text(log.read_text().replace(
                " density=4 raster=1368x896", ""))
            refused = report.assess(base, candidate, log, folder,
                                    view="ws342", density=4)
            self.assertEqual(refused["status"], "unproven")


if __name__ == "__main__":
    unittest.main()
