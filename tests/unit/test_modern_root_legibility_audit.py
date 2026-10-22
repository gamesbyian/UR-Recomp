#!/usr/bin/env python3
"""Run the production Modern root presenter and audit every text draw's
contrast against the pixels actually under it (font independent), then run
the capture diagnostics on the rendered layout. Geometry/contrast evidence of
the real painter, never glyph art, human approval or hardware acceptance."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools import qa_modern_visual_case_checks as cc
from tools import qa_modern_visual_diagnostics as d
from tests.unit.test_qa_modern_visual_diagnostics import p7

ROOT = Path(__file__).resolve().parents[2]
VARIANTS = ("root", "practice", "join", "options", "records", "warning",
            "first-racer", "pause", "pause-controls")
# Native-host composition (root shell + separate destination presenter).
# Its supporting-copy contrast belongs to the destination owner (#2167);
# its geometry is audited here.
DEST_VARIANTS = tuple("dest-" + v for v in VARIANTS[1:]
                      if not v.startswith("pause"))


class ModernRootLegibilityAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            raise unittest.SkipTest("C++ compiler unavailable")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.exe = Path(cls.tmp.name) / "layout-dump"
        build = subprocess.run(
            [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra", "-Werror",
             "-pedantic", "-I", str(ROOT),
             str(ROOT / "tests/native/modern_root_layout_dump.cpp"),
             str(ROOT / "native/product/modern_pause_menu.cpp"),
             "-o", str(cls.exe)], capture_output=True, text=True)
        assert build.returncode == 0, build.stdout + build.stderr

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_text_draw_meets_text_contrast(self):
        for variant in VARIANTS:
            for width in (256, 342):
                run = subprocess.run(
                    [str(self.exe), str(width), str(Path(self.tmp.name) / "x.p7"),
                     variant, "--audit"], capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def visible_text(self, width, variant):
        run = subprocess.run(
            [str(self.exe), str(width), str(Path(self.tmp.name) / "x.p7"),
             variant, "--texts"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        return [l[len("VISIBLE "):] for l in run.stdout.splitlines()
                if l.startswith("VISIBLE ")]

    def test_every_modal_shows_an_exit_hint_and_no_stale_quit_legend(self):
        for variant in ("practice", "join", "options", "records", "warning",
                        "first-racer", "pause",
                        "dest-practice", "dest-join", "dest-options",
                        "dest-records", "dest-warning", "dest-first-racer"):
            for width in (256, 342):
                text = self.visible_text(width, variant)
                self.assertTrue(
                    any(("B " in t or "B/" in t) and
                        any(w in t for w in ("BACK", "CANCEL", "CLEAR", "RESUME"))
                        for t in text), (variant, width, text))
                # B means BACK inside a modal; the root's QUIT legend must
                # not remain visible beneath it.
                self.assertFalse(any("B/ESC QUIT" in t for t in text),
                                 (variant, width))
        root = self.visible_text(342, "root")
        self.assertTrue(any("B/ESC QUIT" in t for t in root))

    def test_native_host_destinations_have_no_clip_or_overlap(self):
        for variant in DEST_VARIANTS:
            for width in (256, 342):
                run = subprocess.run(
                    [str(self.exe), str(width), str(Path(self.tmp.name) / "x.p7"),
                     variant, "--audit"], capture_output=True, text=True)
                geometry = [l for l in run.stdout.splitlines()
                            if l.startswith(("CLIP", "OVERLAP"))]
                self.assertEqual(geometry, [], (variant, width))

    def test_genuine_production_root_passes_its_matrix_case_checks(self):
        """What a real wide/compact root should score: the production root
        painter at its native logical canvas, fitted into each matrix output
        with the shipped 7:6 nearest mapping, then the full case checks."""
        matrix = cc.load_cases()
        for case_id, width in (("root-wide-720", 342), ("root-wide-1080", 342),
                               ("root-43-768", 256), ("root-43-480", 256)):
            out = Path(self.tmp.name) / f"{case_id}.p7"
            run = subprocess.run([str(self.exe), str(width), str(out), "root"])
            self.assertEqual(run.returncode, 0)
            logical = d.load(out)
            grid = [logical.rgb(x, y) for y in range(224) for x in range(width)]
            ow, oh = matrix[case_id]["pixels"]
            m = d.mapping(width, 224, ow, oh)
            cols = [int((x + 0.5 - m.vx) / m.sx) for x in range(ow)]
            rows = []
            for y in range(oh):
                ly = int((y + 0.5 - m.vy) / m.sy)
                if not 0 <= ly < 224:
                    rows += [(0, 0, 0)] * ow
                    continue
                row = grid[ly * width:(ly + 1) * width]
                rows += [row[c] if 0 <= c < width else (0, 0, 0) for c in cols]
            frame = d.Frame(p7(ow, oh, rows))
            report = cc.evaluate(matrix[case_id], frame)
            self.assertTrue(report["pass"], (case_id, report["checks"]))
            self.assertEqual(
                sorted(c["check"] for c in report["checks"]),
                ["action-safe", "logical-width", "output-size", "single-focus-bar"])

    def test_root_layout_within_action_safe_and_single_focus_bar(self):
        for width in (256, 342):
            out = Path(self.tmp.name) / f"root{width}.p7"
            run = subprocess.run([str(self.exe), str(width), str(out), "root"])
            self.assertEqual(run.returncode, 0)
            frame = d.load(out)
            clip = d.clip_audit(frame, width, 224, [
                (255, 255, 255), (200, 200, 200), (248, 248, 0), (160, 208, 248)],
                "action", "integer")  # harness dumps the 1:1 logical canvas
            self.assertTrue(clip["pass"], clip)
            focus = d.focus_audit(frame, (160, 208, 248), 1)
            self.assertTrue(focus["pass"], focus)


if __name__ == "__main__":
    unittest.main()
