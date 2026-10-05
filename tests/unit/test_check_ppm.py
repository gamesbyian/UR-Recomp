from __future__ import annotations

import pathlib
import subprocess
import tempfile
import unittest

from tools.check_ppm import inspect_ppm


ROOT = pathlib.Path(__file__).resolve().parents[2]


class CheckPpmTests(unittest.TestCase):
    def test_inspects_exact_binary_frame(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "frame.ppm"
            path.write_bytes(b"P6\n2 1\n255\n" + b"\0\0\0\x01\x02\x03")
            summary = inspect_ppm(path)
            self.assertEqual((summary.width, summary.height), (2, 1))
            self.assertEqual(summary.unique_rgb, 2)
            self.assertEqual(summary.nonblack_pixels, 1)

    def test_rejects_truncated_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "frame.ppm"
            path.write_bytes(b"P6\n2 1\n255\n\0\0\0")
            with self.assertRaisesRegex(ValueError, "payload length"):
                inspect_ppm(path)

    def test_cli_enforces_dimensions_and_color_floor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "frame.ppm"
            path.write_bytes(b"P6\n2 1\n255\n" + b"\0\0\0\x01\x02\x03")
            result = subprocess.run(
                [
                    "python3", "tools/check_ppm.py", str(path),
                    "--width", "2", "--height", "1", "--min-colors", "2",
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("dimensions=2x1", result.stdout)
            self.assertIn("nonblack_pixels=1/2", result.stdout)


if __name__ == "__main__":
    unittest.main()
