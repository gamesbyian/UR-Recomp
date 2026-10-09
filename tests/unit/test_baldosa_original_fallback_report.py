"""No-guest-mutation and nonempty physical 4x Original fallback evidence."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "baldosa_original_fallback_report",
    ROOT / "tools/baldosa_original_fallback_report.py")
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class BaldosaOriginalFallbackTests(unittest.TestCase):
    def test_two_original_physical_frames_and_crc(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, candidate, log = (root / p for p in ("base", "candidate", "log"))
            lines = ("12345678\n" * 2473).encode()
            base.write_bytes(lines)
            candidate.write_bytes(lines)
            log.write_text("".join(
                f"UR_BALDOSA_ORIGINAL_FALLBACK frame={f} logical=256x224 "
                f"raster=1024x896 pitch=4096 top_changed=0 "
                f"bottom_changed=0 saved=1\n" for f in (450, 520)))
            frames = root / "frames"
            frames.mkdir()
            for f, value in ((450, 8), (520, 16)):
                pixels = bytearray(bytes((value,)) * (1024 * 896 * 4))
                pixels[4096:4100] = bytes((255, 0, 200, 255))
                (frames / f"ur-baldosa-fallback-{f:06d}.pam").write_bytes(
                    report.HEADER + pixels)
            self.assertEqual(report.assess(base, candidate, log, frames)["status"], "passed")
            # Logs with even one subpixel corruption in the nearest fallback
            # cannot substitute for the actual per-view stock copy.
            log.write_text(log.read_text().replace("bottom_changed=0", "bottom_changed=1"))
            self.assertEqual(report.assess(base, candidate, log, frames)["status"], "unproven")
            log.write_text(log.read_text().replace("bottom_changed=1", "bottom_changed=0"))
            candidate.write_bytes(lines.replace(b"12345678", b"99999999", 1))
            self.assertEqual(report.assess(base, candidate, log, frames)["status"], "unproven")
            candidate.write_bytes(lines)
            (frames / "ur-baldosa-fallback-000520.pam").write_bytes(report.HEADER + b"oops")
            with self.assertRaises(ValueError):
                report.assess(base, candidate, log, frames)


if __name__ == "__main__":
    unittest.main()
