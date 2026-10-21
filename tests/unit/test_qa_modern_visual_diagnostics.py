#!/usr/bin/env python3
"""Synthetic-frame contract for the Modern visual diagnostics tool."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from tools import qa_modern_visual_diagnostics as d

BG = (47, 47, 47)
FG = (200, 200, 200)
BAR = (160, 208, 248)


def p7(width, height, pixels):
    head = (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\nMAXVAL 255\n"
            "TUPLTYPE RGB_ALPHA\nENDHDR\n").encode()
    return head + b"".join(bytes((*pixels[i], 255)) for i in range(width * height))


def logical_canvas(w=342, h=224):
    grid = [BG] * (w * h)
    return grid, w, h


def render(grid, lw, lh, out_w, out_h):
    f, vx, vy, _, _ = d.integer_scale(lw, lh, out_w, out_h)
    out = [(0, 0, 0)] * (out_w * out_h)
    for y in range(out_h):
        for x in range(out_w):
            lx, ly = (x - vx) // f, (y - vy) // f
            if 0 <= lx < lw and 0 <= ly < lh and x >= vx and y >= vy:
                out[y * out_w + x] = grid[ly * lw + lx]
    return d.Frame(p7(out_w, out_h, out))


def put(grid, lw, x, y, w, h, c):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            grid[yy * lw + xx] = c


class DiagnosticsTest(unittest.TestCase):
    def test_scale_and_safe_area_mirror_native_header(self):
        self.assertEqual(d.integer_scale(342, 224, 1280, 720), (3, 127, 24, 1026, 672))
        self.assertEqual(d.integer_scale(342, 224, 3840, 2160)[0], 9)
        self.assertEqual(d.integer_scale(256, 224, 1024, 768)[0], 3)
        self.assertIsNone(d.integer_scale(342, 224, 300, 700))
        self.assertEqual(d.title_safe(342, 224), (18, 12, 306, 200))
        self.assertEqual(d.action_safe(256, 224), (7, 6, 242, 212))
        self.assertIsNone(d.title_safe(10, 10))

    def test_multi_resolution_logical_equivalence(self):
        grid, w, h = logical_canvas()
        put(grid, w, 30, 30, 40, 8, FG)
        a = render(grid, w, h, 1280, 720)
        b = render(grid, w, h, 1920, 1080)
        rep = d.compare_resolutions(a, b, w, h)
        self.assertTrue(rep["pass"], rep)
        self.assertEqual((rep["a"]["factor"], rep["b"]["factor"]), (3, 4))
        put(grid, w, 100, 100, 2, 1, FG)
        c = render(grid, w, h, 1920, 1080)
        rep = d.compare_resolutions(a, c, w, h)
        self.assertFalse(rep["pass"])
        self.assertEqual(rep["differing_logical_pixels"], 2)
        self.assertEqual(rep["difference_bbox"], [100, 100, 102, 101])

    def test_blur_is_detected_as_nonuniform_blocks(self):
        grid, w, h = logical_canvas()
        put(grid, w, 30, 30, 40, 8, FG)
        a = render(grid, w, h, 1280, 720)
        pixels = [a.rgb(x, y) for y in range(a.height) for x in range(a.width)]
        pixels[(24 + 30 * 3) * a.width + 127 + 30 * 3] = (1, 2, 3)
        blurred = d.Frame(p7(a.width, a.height, pixels))
        self.assertGreater(d.extract_logical(blurred, w, h)["nonuniform_blocks"], 0)

    def test_clip_inside_and_outside_safe_area(self):
        grid, w, h = logical_canvas()
        put(grid, w, 30, 30, 40, 8, FG)
        ok = d.clip_audit(render(grid, w, h, 1280, 720), w, h, [FG])
        self.assertTrue(ok["pass"], ok)
        put(grid, w, 12, 100, 20, 8, FG)  # intrudes into title-unsafe margin
        bad = d.clip_audit(render(grid, w, h, 1280, 720), w, h, [FG])
        self.assertFalse(bad["pass"])
        self.assertTrue(d.clip_audit(render(grid, w, h, 1280, 720), w, h, [FG],
                                     "action")["pass"])
        put(grid, w, 0, 100, 4, 8, FG)  # touches viewport edge: clipped
        edge = d.clip_audit(render(grid, w, h, 1280, 720), w, h, [FG], "action")
        self.assertFalse(edge["pass"])
        self.assertGreater(edge["viewport_edge_pixels"], 0)
        with self.assertRaises(ValueError):
            d.clip_audit(render(grid, w, h, 1280, 720), w, h, [(9, 9, 9)])

    def test_focus_requires_exactly_one_bar(self):
        grid, w, h = logical_canvas(256, 224)
        self.assertFalse(d.focus_audit(render(grid, w, h, 1024, 768), BAR, 3)["pass"])
        put(grid, w, 20, 60, 3, 16, BAR)
        rep = d.focus_audit(render(grid, w, h, 1024, 768), BAR, 3)
        self.assertTrue(rep["pass"], rep)
        self.assertEqual(len(rep["bars"]), 1)
        put(grid, w, 20, 100, 3, 16, BAR)
        self.assertFalse(d.focus_audit(render(grid, w, h, 1024, 768), BAR, 3)["pass"])

    def test_local_contrast_flags_low_contrast_text(self):
        grid, w, h = logical_canvas()
        put(grid, w, 30, 30, 40, 8, (152, 152, 152))
        put(grid, w, 50, 20, 8, 30, (80, 80, 80))
        frame = render(grid, w, h, 1280, 720)
        roi = (127 + 90, 24 + 60, 127 + 3 * 80, 24 + 3 * 60)
        low = d.local_contrast(frame, roi, (152, 152, 152))
        self.assertFalse(low["pass"])
        self.assertLess(low["worst_ratio"], 4.5)
        grid2, _, _ = logical_canvas()
        put(grid2, w, 30, 30, 40, 8, (200, 200, 200))
        put(grid2, w, 50, 20, 8, 30, (80, 80, 80))
        good = d.local_contrast(render(grid2, w, h, 1280, 720), roi, (200, 200, 200))
        self.assertTrue(good["pass"], good)

    def test_provenance_pin_and_cli(self):
        grid, w, h = logical_canvas()
        put(grid, w, 30, 30, 40, 8, FG)
        frame = render(grid, w, h, 1280, 720)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "f.p7"
            path.write_bytes(p7(frame.width, frame.height,
                                [frame.rgb(x, y) for y in range(frame.height)
                                 for x in range(frame.width)]))
            argv = ["clip", str(path), "--logical", "342", "224",
                    "--colour", "#c8c8c8", "--require"]
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(d.main(argv + ["--expect-sha256", frame.sha256]), 0)
            self.assertEqual(json.loads(out.getvalue())["input_sha256"], frame.sha256)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(d.main(argv + ["--expect-sha256", "0" * 64]), 1)
            report = json.loads(out.getvalue())
            self.assertFalse(report["human_visual_approved"])
            self.assertEqual(report["release_gate_credit"], 0)


if __name__ == "__main__":
    unittest.main()
