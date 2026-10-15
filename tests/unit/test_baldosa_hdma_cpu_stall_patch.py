import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_hdma_cpu_stall_patch as fix  # noqa: E402

# Verbatim baldosa/snesrecomp@075fbe4 regions, joined by filler lines.
PINNED_INFRA = '#include "snes/snes.h"\n/* ... */\n' + fix.PINNED_INFRA
PINNED_DRIVER = "/* ... */\n" + fix.PINNED_DRIVER
assert fix.PINNED_INFRA == 'void snes_refresh_exempt(void) { g_refresh_charged_upto = g_cpu.master_cycles; }\nvoid snes_refresh_charge(void) {\n  uint64_t m = g_cpu.master_cycles;\n'
assert fix.PINNED_DRIVER == '    frame_end = g_snes->beamMasterLast +\n                (to_vblank ? to_vblank : BFD_MASTER_CYCLES_PER_FIELD);\n  }\n'

FIELD = 357368
LINE = 1364
HARNESS = r"""
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
typedef uint8_t uint8;
typedef struct { uint8_t bAdr; uint16_t aAdr; uint8_t aBank; uint16_t size; uint8_t indBank;
  uint8_t mode; bool indirect; } DmaChannel;
typedef struct { DmaChannel channel[8]; } Dma;
typedef struct { Dma *dma; } Snes;
static Dma g_dma; static Snes g_snes_obj = {&g_dma}; static Snes *g_snes = &g_snes_obj;
static struct { uint64_t master_cycles; } g_cpu;
uint8 g_snesrecomp_last_hdmaen;
static uint8_t wram[0x20000];
#define LINE 1364ull
static uint8_t snes_read(Snes *s, uint32_t adr) { (void)s; return wram[adr & 0x1ffff]; }
MODULE
int main(void) {
  /* Six live channels ($BE), each table: 112 lines, then 112 lines, then end. */
  g_snesrecomp_last_hdmaen = 0xBE;
  for (int i = 1; i < 8; i++) {
    if (!((0xBE >> i) & 1)) continue;
    g_dma.channel[i].aBank = 0x7E; g_dma.channel[i].aAdr = (uint16_t)(0x2000 + i * 16);
    g_dma.channel[i].mode = (i == 3) ? 3 : 0;
    uint8_t *t = &wram[0x2000 + i * 16];
    t[0] = 112; t[1] = 0; t[2] = 0; t[3] = 0; t[4] = 0; t[5] = 112; t[6] = 0; t[7] = 0; t[8] = 0; t[9] = 0; t[10] = 0;
  }
  /* Channel 7: repeat mode, two bytes per line for the whole field. */
  g_dma.channel[7].mode = 2; wram[0x2000 + 7 * 16] = 0xFF; wram[0x2000 + 7 * 16 + 255] = 0;
  uint64_t start = 1000000;
  ur_hdma_stall_field_begin(start);
  g_cpu.master_cycles = start + 37ull * LINE;            /* just before V=0 init */
  ur_hdma_pass(true);
  uint64_t before_init = g_cpu.master_cycles;
  g_cpu.master_cycles = start + 37ull * LINE + 13;       /* past init */
  ur_hdma_pass(true);
  printf("%llu ", (unsigned long long)(g_cpu.master_cycles - (start + 37ull * LINE + 13)));
  (void)before_init;
  for (int line = 0; line < 3; line++) {
    uint64_t t = start + (37ull + line) * LINE + 1104;
    g_cpu.master_cycles = t;
    ur_hdma_pass(true);
    printf("%llu ", (unsigned long long)(g_cpu.master_cycles - t));
  }
  /* Parked: pass line 3..9 without charging. */
  g_cpu.master_cycles = start + (37ull + 9) * LINE + 1104;
  uint64_t parked = g_cpu.master_cycles;
  ur_hdma_pass(false);
  printf("%llu\n", (unsigned long long)(g_cpu.master_cycles - parked));
  return 0;
}
"""


def module_source():
    """The staged HDMA module, cut from the corrected refresh hook."""
    staged = fix.patch_infra(PINNED_INFRA)
    body = staged[staged.index("/* " + fix.MARK):staged.index("void snes_refresh_exempt")]
    return body


class PatchTest(unittest.TestCase):
    def test_corrects_pinned_sources_once(self):
        infra = fix.patch_infra(PINNED_INFRA)
        driver = fix.patch_driver(PINNED_DRIVER)
        self.assertIn('#include "snes/dma.h"', infra)
        self.assertEqual(infra.count("ur_hdma_pass("), 3)
        self.assertIn("ur_hdma_stall_field_begin(frame_end - BFD_MASTER_CYCLES_PER_FIELD)", driver)
        self.assertEqual(fix.patch_infra(infra), infra)
        self.assertEqual(fix.patch_driver(driver), driver)

    def test_rejects_unknown_revision_and_tampering(self):
        with self.assertRaisesRegex(ValueError, "not recognized"):
            fix.patch_infra(PINNED_INFRA.replace("uint64_t m = g_cpu", "uint64_t n = g_cpu"))
        with self.assertRaisesRegex(ValueError, "not recognized"):
            fix.patch_driver(PINNED_DRIVER.replace("to_vblank ?", "to_vblank != 0 ?"))
        with self.assertRaisesRegex(ValueError, "altered"):
            fix.patch_driver(fix.patch_driver(PINNED_DRIVER).replace("frame_end -", "frame_end +"))


@unittest.skipUnless(shutil.which("cc") or shutil.which("gcc"), "needs a C compiler")
class StallCostTest(unittest.TestCase):
    def test_line_costs_match_hardware_formula(self):
        cc = shutil.which("cc") or shutil.which("gcc")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "t.c").write_text(HARNESS.replace("MODULE", module_source()))
            subprocess.run([cc, "-std=c99", "-O2", "-Wall", "-Werror", "-Wno-unused-function",
                            str(tmp / "t.c"), "-o", str(tmp / "t")], check=True)
            out = subprocess.run([str(tmp / "t")], check=True, capture_output=True,
                                 text=True).stdout.split()
        init, line0, line1, line2, parked = map(int, out)
        # V=0: 18 + 8 per live channel (six).
        self.assertEqual(init, 18 + 6 * 8)
        # Line 0: 18 + 8 x 6 live; the five non-repeat channels (four 1-byte, one 4-byte) move their first
        # entry (1 or 4 bytes); the repeat channel 7 moves 2 bytes every line.
        self.assertEqual(line0, 18 + 6 * 8 + 8 * (1 + 1 + 4 + 1 + 1 + 2))
        # Later lines: only the repeat channel transfers -- the RF-019 66 + its 16.
        self.assertEqual(line1, 18 + 6 * 8 + 8 * 2)
        self.assertEqual(line2, 18 + 6 * 8 + 8 * 2)
        self.assertEqual(parked, 0)


if __name__ == "__main__":
    unittest.main()
