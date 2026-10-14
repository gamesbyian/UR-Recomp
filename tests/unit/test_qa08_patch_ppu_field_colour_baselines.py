"""Synthetic, fail-closed pinned PPU journal source-only diagnostic patch."""
import tempfile
import unittest
from pathlib import Path
from tools.qa08_patch_ppu_field_colour_baselines import patch_source, apply

HEADER = """// -- START OF SNAPSHOT, 0x40 bytes
  uint8 inidisp;
  uint16 fixedColor;
  uint8 cgadsub;
  uint8 cgwsel;
  // -- END OF SNAPSHOT
"""
SOURCE = r'''static int raster_dump_field(char *out, int cap, const char *name,
                             const PpuRasterField *f) {
  int pos = 0;
  int i;
#define RJ_OFF(field) (offsetof(Ppu, field) - offsetof(Ppu, inidisp))
  uint16_t bg1h, bg1v;
  memcpy(&bg1h, f->regs + RJ_OFF(hScroll), sizeof(bg1h));
  memcpy(&bg1v, f->regs + RJ_OFF(vScroll), sizeof(bg1v));
  pos += snprintf(out + pos, cap - pos,
                  "\"%s\":{\"count\":%d,\"dropped\":%u,"
                  "\"base\":{\"inidisp\":\"0x%02X\",\"tm\":\"0x%02X\","
                  "\"tmw\":\"0x%02X\",\"cgadsub\":\"0x%02X\","
                  "\"bg1h\":%u,\"bg1v\":%u},\"entries\":[",
                  name, f->count, (unsigned)f->dropped,
                  f->regs[RJ_OFF(inidisp)], f->regs[RJ_OFF(screenEnabled)],
                  f->regs[RJ_OFF(screenWindowed)], f->regs[RJ_OFF(cgadsub)],
                  (unsigned)bg1h, (unsigned)bg1v);
#undef RJ_OFF
}
int ppu_rasterDebugDump(char *out, int cap) { return 0; }
'''

class Qa08FieldBaselinePatchTest(unittest.TestCase):
    def test_saved_fields_added_to_debug_only(self):
        patched = patch_source(SOURCE, HEADER)
        self.assertIn('memcpy(&fixed15, f->regs + RJ_OFF(fixedColor)', patched)
        self.assertIn('f->regs[RJ_OFF(cgwsel)], (unsigned)fixed15', patched)
        self.assertIn(r'\"cgwsel\":\"0x%02X\",\"fixed15\":\"0x%04X\"', patched)
        self.assertEqual(patched.count('int ppu_rasterDebugDump('), 1)
        with self.assertRaisesRegex(ValueError, 'already-patched'):
            patch_source(patched, HEADER)

    def test_layout_and_printer_drift_rejected(self):
        with self.assertRaisesRegex(ValueError, 'layout'):
            patch_source(SOURCE, HEADER.replace('uint16 fixedColor;', 'uint16 badField;'))
        with self.assertRaisesRegex(ValueError, 'unexpected'):
            patch_source(SOURCE.replace('  uint16_t bg1h, bg1v;', '  uint16_t bg1h;'), HEADER)

    def test_dry_run_and_exact_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'runner/src/snes'
            p.mkdir(parents=True)
            (p / 'ppu.h').write_text(HEADER, encoding='utf-8')
            c = p / 'ppu.c'
            c.write_text(SOURCE, encoding='utf-8')
            apply(Path(tmp), check_only=True)
            self.assertEqual(c.read_text(), SOURCE)
            apply(Path(tmp))
            self.assertNotEqual(c.read_text(), SOURCE)
            with self.assertRaisesRegex(ValueError, 'already-patched'):
                apply(Path(tmp))

if __name__ == '__main__':
    unittest.main()
