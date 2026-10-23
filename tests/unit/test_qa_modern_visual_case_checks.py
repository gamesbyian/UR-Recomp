#!/usr/bin/env python3
"""The case planner covers the whole frozen matrix and judges synthetic frames."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from tests.unit.test_qa_modern_visual_diagnostics import (
    BAR, FG, logical_canvas, p7, put, render_fit)
from tools import qa_modern_visual_case_checks as cc
from tools import qa_modern_visual_diagnostics as d


def busy(w):
    """Dense deterministic 1px texture inside the action-safe region (like
    real UI art), so only the true logical width yields uniform blocks."""
    grid, _, h = logical_canvas(w, 224)
    seed = 12345
    for y in range(20, 200):
        for x in range(24, w - 24):
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            if (seed >> 16) % 3 == 0:
                grid[y * w + x] = FG if (seed >> 8) % 2 else (90, 40, 60)
    return grid, h


def put_band(grid, w, x, y, h=16):
    """Focus bar plus the shared band's two-tone ring beside it."""
    put(grid, w, x, y, 40, 1, d.FOCUS_RING_DARK)
    put(grid, w, x, y + h - 1, 40, 1, d.FOCUS_RING_DARK)
    put(grid, w, x, y + 1, 40, 1, d.FOCUS_RING_LIGHT)
    put(grid, w, x, y + h - 2, 40, 1, d.FOCUS_RING_LIGHT)
    put(grid, w, x, y, 3, h, BAR)


class CaseChecksTest(unittest.TestCase):
    def test_every_matrix_case_has_a_plan(self):
        cases = cc.load_cases()
        self.assertEqual(len(cases), 25)
        for case in cases.values():
            plan = cc.plan(case)
            self.assertIn(plan["logical"][0], (256, 342))
            self.assertEqual(plan["output"], case["pixels"])
        self.assertTrue(cc.plan(cases["root-wide-720"])["check_clip"])
        self.assertTrue(cc.plan(cases["root-wide-720"])["check_focus"])
        self.assertFalse(cc.plan(cases["title-wide-1080"])["check_clip"])
        self.assertFalse(cc.plan(cases["authentic-stock-wide"])["check_clip"])
        self.assertEqual(cc.plan(cases["title-compact-43"])["logical"], [256, 224])
        self.assertEqual(cc.plan(cases["root-wide-4k-virtual"])["output"], [3840, 2160])

    def test_genuine_wide_root_passes_and_wrong_size_or_width_fails(self):
        case = cc.load_cases()["root-wide-720"]
        grid, h = busy(342)
        put_band(grid, 342, 12, 60)
        ok = cc.evaluate(case, render_fit(grid, 342, h, 1280, 720))
        self.assertTrue(ok["pass"], ok)
        self.assertEqual(ok["release_gate_credit"], 0)
        self.assertEqual(
            sorted(c["check"] for c in ok["checks"]),
            ["action-safe", "focus-ring", "logical-width", "output-size",
             "single-focus-bar"])
        # right canvas, wrong output size
        bad = cc.evaluate(case, render_fit(grid, 342, h, 1920, 1080))
        self.assertFalse(bad["pass"])
        self.assertFalse(next(c for c in bad["checks"]
                              if c["check"] == "output-size")["pass"])
        # a 256-wide source stretched into the 16:9 slot is not a wide source
        narrow, nh = busy(256)
        put_band(narrow, 256, 12, 60)
        stretched = cc.evaluate(case, render_fit(narrow, 256, nh, 1280, 720))
        self.assertFalse(next(c for c in stretched["checks"]
                              if c["check"] == "logical-width")["pass"])
        # no focus bar / two focus bars both fail
        grid2, _ = busy(342)
        none = cc.evaluate(case, render_fit(grid2, 342, h, 1280, 720))
        self.assertFalse(next(c for c in none["checks"]
                              if c["check"] == "single-focus-bar")["pass"])
        put_band(grid, 342, 12, 120)
        two = cc.evaluate(case, render_fit(grid, 342, h, 1280, 720))
        self.assertFalse(next(c for c in two["checks"]
                              if c["check"] == "single-focus-bar")["pass"])

    def test_missing_ring_is_advisory_unless_required(self):
        case = cc.load_cases()["root-wide-720"]
        grid, h = busy(342)
        put(grid, 342, 12, 60, 3, 16, BAR)  # legacy bar, no ring
        frame = render_fit(grid, 342, h, 1280, 720)
        self.assertTrue(cc.evaluate(case, frame)["pass"])
        strict = cc.evaluate(case, frame, require_ring=True)
        self.assertFalse(strict["pass"])
        self.assertEqual([c["check"] for c in strict["checks"] if not c["pass"]],
                         ["focus-ring"])

    def test_compact_43_and_title_cases(self):
        cases = cc.load_cases()
        grid, h = busy(256)
        put_band(grid, 256, 12, 60)
        self.assertTrue(cc.evaluate(cases["root-43-768"],
                                    render_fit(grid, 256, h, 1024, 768))["pass"])
        # title: size + width only (different palette, no focus bar expected)
        grid, h = busy(342)
        rep = cc.evaluate(cases["title-wide-1080"], render_fit(grid, 342, h, 1920, 1080))
        self.assertEqual(sorted(c["check"] for c in rep["checks"]),
                         ["logical-width", "output-size"])
        self.assertTrue(rep["pass"], rep)

    def test_cli_pins_hash_and_rejects_unknown_case(self):
        grid, h = busy(342)
        put_band(grid, 342, 12, 60)
        frame = render_fit(grid, 342, h, 1280, 720)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "f.p7"
            path.write_bytes(p7(frame.width, frame.height,
                                [frame.rgb(x, y) for y in range(frame.height)
                                 for x in range(frame.width)]))
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(cc.main(["root-wide-720", str(path), "--require",
                                          "--expect-sha256", frame.sha256]), 0)
            self.assertTrue(json.loads(out.getvalue())["pass"])
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cc.main(["nope", str(path)]), 1)
                self.assertEqual(cc.main(["root-wide-720", str(path),
                                          "--expect-sha256", "0" * 64]), 1)


if __name__ == "__main__":
    unittest.main()
