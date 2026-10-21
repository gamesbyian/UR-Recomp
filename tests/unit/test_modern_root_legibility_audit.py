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

from tools import qa_modern_visual_diagnostics as d

ROOT = Path(__file__).resolve().parents[2]
VARIANTS = ("root", "practice", "join", "options", "records", "warning")


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

    def test_root_layout_within_action_safe_and_single_focus_bar(self):
        for width in (256, 342):
            out = Path(self.tmp.name) / f"root{width}.p7"
            run = subprocess.run([str(self.exe), str(width), str(out), "root"])
            self.assertEqual(run.returncode, 0)
            frame = d.load(out)
            clip = d.clip_audit(frame, width, 224, [
                (255, 255, 255), (200, 200, 200), (248, 248, 0), (160, 208, 248)],
                "action")
            self.assertTrue(clip["pass"], clip)
            focus = d.focus_audit(frame, (160, 208, 248), 1)
            self.assertTrue(focus["pass"], focus)


if __name__ == "__main__":
    unittest.main()
