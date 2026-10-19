"""Fail-closed QA08 native *span* compositor source observer tests.

No ROM and no guest execution: validates the exact integration seams so that
the future Windows trial cannot silently collect the legacy-only path.
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import qa08_late_effective_span_probe as span

BASE = ("#include <stdio.h>\n#include <stdlib.h>\n"
        "static NOINLINE void PpuDrawWholeLine(Ppu *ppu, uint y) {\n"
        "  /* actual selected zbuffers, colour windows and math exist here */\n"
        + span.ANCHOR)


class SpanEffectiveObserverTest(unittest.TestCase):
    def test_renderer_branch_and_real_span_anchor(self):
        self.assertEqual(span.GAME_REV, "10b864b9d14a7b7416dd909eb7b054c88faef101")
        self.assertEqual(span.CORE_REV, "075fbe4c8e0d97b0013be541795c39cb644a9709")
        self.assertEqual(span.RELATIVE.as_posix(), "snesrecomp/runner/src/snes/ppu.c")
        self.assertIn("kPpuRenderFlags_NewRenderer", span.TRACE)
        self.assertIn("PpuPixelColor(ppu, ppu->bgBuffers[0].data[i], i)", span.TRACE)
        self.assertIn("rendered_subscreen", span.TRACE)
        self.assertIn("UR_QA08_LATE_SPAN_SOURCE", span.TRACE)
        self.assertIn("UR_QA08_LATE_SPAN_FINAL", span.TRACE)
        self.assertIn("UR_QA08_LATE_SPAN_OBJECT_OVERRIDE", span.TRACE)
        self.assertIn("x + ppu->extraLeftRight", span.TRACE)
        self.assertIn("x + kPpuExtraLeftRight", span.TRACE)
        self.assertEqual(set(span.POINTS),
                         {(70,58),(202,182),(84,77),(175,145),
                          (53,41),(187,160),(65,52),(190,161)})

    def test_additive_exact_source_transform_and_idempotence(self):
        output=span.patch_source(BASE)
        self.assertEqual(span.patch_source(output), output)
        self.assertEqual(output.count(span.MARK),1)
        self.assertIn(span.TRACE + span.ANCHOR, output)
        self.assertIn("/* actual selected zbuffers",output)
        self.assertEqual(output.replace(span.TRACE,""), BASE)
        self.assertNotIn("ppu_write(ppu,",span.TRACE)
        self.assertNotIn("PpuDrawBackgrounds(ppu,",span.TRACE)
        self.assertNotIn("PpuDrawWholeLine(ppu,",span.TRACE)

    def test_source_anchor_drift_partial_duplication_and_competing_probes_refused(self):
        candidates=(BASE.replace(span.ANCHOR,""),BASE+span.ANCHOR,
                    BASE.replace("static NOINLINE void PpuDrawWholeLine", "void PpuDrawWholeLine"),
                    BASE.replace(span.ANCHOR,span.ANCHOR.replace("  PpuWriteOverlayRenderLine","  PpuWriteOverlayRenderLINE")),
                    BASE+"UR_QA08_LATE_SPAN_SOURCE")
        for bad in candidates:
            with self.subTest(bad=bad[-80:]):
                with self.assertRaisesRegex(ValueError,"anchor|competing"):
                    span.patch_source(bad)
        good=span.patch_source(BASE)
        for bad in (good.replace(span.TRACE,""),
                    good.replace("cgram6c=%04x","cgram6b=%04x"),
                    good + span.TRACE):
            # A stripped observer is a clean original; an altered/duplicate
            # observer is never allowed to claim idempotence.
            if bad == BASE: continue
            with self.assertRaisesRegex(ValueError,"partial or changed"):
                span.patch_source(bad)

    def test_pinned_game_generated_source_and_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d)
            target=game/span.RELATIVE
            target.parent.mkdir(parents=True)
            (game/"src/gen").mkdir(parents=True)
            generated=game/"src/gen/dispatch_v2.c"
            generated.write_text("generated\n")
            target.write_text(BASE)
            def versions(path):
                return span.CORE_REV if path == game/"snesrecomp" else span.GAME_REV
            with patch.object(span, "pinned_revision", side_effect=versions):
                self.assertEqual(span.apply_game(game,write=False),target)
                self.assertEqual(target.read_text(),BASE)
                span.apply_game(game,write=True)
                self.assertEqual(target.read_text(),span.patch_source(BASE))
                span.apply_game(game,write=True)
            target.write_text(BASE)
            with patch.object(span, "pinned_revision", return_value="wrong"):
                with self.assertRaisesRegex(ValueError, "revision changed"):
                    span.apply_game(game,write=True)
            generated.unlink()
            with patch.object(span, "pinned_revision", side_effect=versions):
                with self.assertRaisesRegex(ValueError,"guest missing"):
                    span.apply_game(game,write=True)
            self.assertEqual(target.read_text(),BASE)

    def test_static_C_formatstrings_have_no_unescaped_newlines(self):
        # C format strings must contain backslash-n, not a real line break
        # between the start/end quotation marks.
        self.assertIn("rgb555=%04x\\n\"",span.TRACE)
        self.assertIn("cgwsel=%02x\\n\"",span.TRACE)
        self.assertIn("ts=%02x\\n\"",span.TRACE)
        self.assertNotIn("rgb555=%04x\n\"",span.TRACE)
        self.assertNotIn("cgwsel=%02x\n\"",span.TRACE)

    def test_unavailable_game_direct_cli_fails_closed(self):
        out=subprocess.run([sys.executable,str(ROOT/"tools/qa08_late_effective_span_probe.py"),
                            "--game",str(ROOT/"qa08-absent-baldosa")],
                           cwd=ROOT,check=False,capture_output=True,text=True)
        self.assertEqual(out.returncode,2)
        self.assertIn("QA08_SPAN_EFFECTIVE_PPU_REFUSED:",out.stderr)


if __name__ == "__main__":
    unittest.main()
