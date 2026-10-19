"""Fail-closed ROM-free tests for unexecuted graphics PPU observer trial."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import qa08_late_effective_cgram_probe as probe


BASE = (probe.HEADER +
        '\nstatic void ppu_render_pixel(Ppu *ppu, int x, int y) {\n' +
        '  /* original compositor retained */\n' + probe.FINAL + '}\n' +
        'static int ppu_resolve_pixel(Ppu *ppu, int x, int y, bool sub, int *r, int *g, int *b) {\n' +
        '  /* original selected-color resolver retained */\n' + probe.RESOLVER + '}\n')


class ExactSourceProbe(unittest.TestCase):
    def test_static_raw_pixel_anchors_and_renderer_y_offset(self):
        self.assertEqual(len(probe.POINTS), 8)
        self.assertEqual(set(probe.POINTS), {
            (70,58),(202,182),(84,77),(175,145),
            (53,41),(187,160),(65,52),(190,161)
        })
        self.assertIn('snes_frame_counter >= 5176', probe.PREDICATE)
        self.assertIn('snes_frame_counter <= 5186', probe.PREDICATE)
        self.assertIn('logical_y=%d ppu_line=%d',probe.RESOLVER_TRACE)
        for x,y in probe.POINTS:
            self.assertIn(f'(x == {x} && y == {y+1})',probe.PREDICATE)
        self.assertNotIn('y == 58)',probe.PREDICATE)

    def test_idempotent_exact_additive_transform(self):
        after=probe.patch_source(BASE)
        self.assertEqual(probe.patch_source(after),after)
        self.assertEqual(after.count(probe.MARK_RESOLVER),1)
        self.assertEqual(after.count(probe.MARK_FINAL),1)
        self.assertIn(probe.RESOLVER_TRACE,after)
        self.assertIn(probe.FINAL_TRACE,after)
        self.assertIn('/* original selected-color resolver retained */',after)
        self.assertIn('/* original compositor retained */',after)
        self.assertIn('  return layer;\n',after)
        self.assertIn('  pixelBuffer[3] = 0;\n',after)
        self.assertIn('(unsigned)ppu->cgram[qa08_index]', after)
        self.assertIn('selected_rgb555=%04x', after)
        self.assertIn('directcolor=%u', after)
        self.assertIn('bit_depths_per_mode[actMode][layer] == 8', after)
        self.assertIn('RGB8=%u,%u,%u', after)

    def test_missing_duplicate_partial_and_competing_source_refused(self):
        for broken in (BASE.replace(probe.RESOLVER, ''),
                       BASE.replace(probe.FINAL, ''),
                       BASE + probe.RESOLVER,
                       BASE.replace(probe.HEADER,''),
                       BASE+'\nUR_QA08_NATIVE_EFFECTIVE_PIXEL_OWNER\n',
                       BASE+'\n#include <stdio.h>\n'):
            with self.subTest(broken=broken[-40:]):
                with self.assertRaisesRegex(ValueError,'pinned original'):
                    probe.patch_source(broken)
        ready=probe.patch_source(BASE)
        for broken in (ready.replace(probe.FINAL_TRACE, ''),
                       ready.replace(probe.RESOLVER_TRACE, ''),
                       ready.replace('cgram6c=%04x','cgram6b=%04x')):
            with self.assertRaisesRegex(ValueError,'partial or modified'):
                probe.patch_source(broken)

    def test_dry_run_pinned_revisions_and_generated_guest_guard(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            source_file=root/probe.RELATIVE
            source_file.parent.mkdir(parents=True)
            (root/'src/gen').mkdir(parents=True)
            (root/'src/gen/dispatch_v2.c').write_text('generated\n')
            source_file.write_text(BASE)
            def revisions(p):
                return probe.GAME_REV if p==root else probe.CORE_REV
            with patch.object(probe,'pinned_revision',side_effect=revisions):
                path=probe.apply_game(root,write=False)
                self.assertEqual(path,source_file)
                self.assertEqual(source_file.read_text(), BASE)
                probe.apply_game(root,write=True)
                self.assertIn(probe.MARK_RESOLVER,source_file.read_text())
                probe.apply_game(root,write=True)
            source_file.write_text(BASE)
            with patch.object(probe,'pinned_revision',return_value='bad revision'):
                with self.assertRaisesRegex(ValueError,'revision differs'):
                    probe.apply_game(root,write=True)
            self.assertEqual(source_file.read_text(), BASE)
            (root/'src/gen/dispatch_v2.c').unlink()
            with patch.object(probe,'pinned_revision',side_effect=revisions):
                with self.assertRaisesRegex(ValueError,'guest was not found'):
                    probe.apply_game(root,write=True)

    def test_no_warranted_runtime_noninterference_or_gate_credit(self):
        after=probe.patch_source(BASE)
        self.assertIn('getenv("UR_QA08_LATE_EFFECTIVE_PIXEL_TRACE")',after)
        self.assertIn('fprintf(stderr',after)
        self.assertNotIn('ppu_write(',probe.RESOLVER_TRACE+probe.FINAL_TRACE)
        self.assertNotIn('ppu_resolve_pixel(',probe.RESOLVER_TRACE+probe.FINAL_TRACE)
        self.assertEqual(probe.GAME_REV,"10b864b9d14a7b7416dd909eb7b054c88faef101")
        self.assertEqual(probe.CORE_REV,"075fbe4c8e0d97b0013be541795c39cb644a9709")
        self.assertIn('noninterference',probe.__doc__)
        self.assertIn('unproven',probe.__doc__)

    def test_bad_direct_cli_fails_closed(self):
        out=subprocess.run([sys.executable,str(ROOT/'tools/qa08_late_effective_cgram_probe.py'),
                            '--game',str(ROOT/'nonexistent-git-checkout')],
                           cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(out.returncode,2)
        self.assertIn('QA08_LATE_EFFECTIVE_PROBE_REFUSED:',out.stderr)

if __name__=='__main__': unittest.main()
