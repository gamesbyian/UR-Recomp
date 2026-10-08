import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import check_paused_overlay_dump as check  # noqa: E402


def ppm(width, height, pixel_at):
    payload = bytearray()
    for y in range(height):
        for x in range(width):
            payload.extend(pixel_at(x, y))
    return b"P6\n%d %d\n255\n" % (width, height) + bytes(payload)


def race_like(x, y):
    # Colourful field: never a dark neutral grey.
    return bytes(((x * 7) % 200 + 40, (y * 5) % 180 + 50, 120))


def with_panel(x, y):
    if 40 <= x < 216 and 50 <= y < 174:
        return b"\x22\x22\x22"
    return race_like(x, y)


class CheckPausedOverlayDumpTests(unittest.TestCase):
    def run_check(self, data, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "paused.ppm"
            if data is not None:
                path.write_bytes(data)
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
                code = check.main([str(path), *extra])
            return code, out.getvalue()

    def test_panel_over_frozen_field_passes(self):
        code, out = self.run_check(ppm(256, 224, with_panel))
        self.assertEqual(code, 0, out)
        self.assertIn("centre_panel_fraction=1.000", out)

    def test_bare_frozen_field_fails(self):
        code, out = self.run_check(ppm(256, 224, race_like))
        self.assertEqual(code, 1)
        self.assertIn("carries no modal panel", out)

    def test_missing_dump_fails(self):
        code, out = self.run_check(None)
        self.assertEqual(code, 1)
        self.assertIn("missing", out)

    def test_truncated_payload_fails(self):
        code, out = self.run_check(ppm(256, 224, with_panel)[:-10])
        self.assertEqual(code, 1)
        self.assertIn("payload does not match", out)

    def test_wrong_magic_fails(self):
        data = ppm(8, 8, with_panel).replace(b"P6", b"P3", 1)
        code, _ = self.run_check(data)
        self.assertEqual(code, 1)

    def test_measured_dumps_classify(self):
        # Scaled presents keep the same centre-panel geometry.
        code, _ = self.run_check(
            ppm(512, 448, lambda x, y: with_panel(x // 2, y // 2)))
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
