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
