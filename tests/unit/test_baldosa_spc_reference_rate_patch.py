import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_spc_reference_rate_patch as fix  # noqa: E402

# Verbatim baldosa/snesrecomp@075fbe4 runner/src/apu_frame_clock.h.
PINNED_HEADER = '#pragma once\n#include <stdint.h>\n\n#define RTL_MASTER_CYCLES_PER_FRAME 357368ull\n#define RTL_APU_CYCLES_PER_FRAME 17088ull\n\n/* A host iteration can include an NMI-disabled loader spanning many hardware\n * frames. Keep its elapsed time when beginning the following iteration. */\ntypedef struct RtlApuFrameClock {\n  uint64_t start_master, start_guest, next_guest, last_duration;\n} RtlApuFrameClock;\n\nstatic inline void rtl_apu_clock_begin(RtlApuFrameClock *clock, uint64_t master) {\n  clock->start_master = master;\n  clock->start_guest = clock->next_guest;\n}\n\nstatic inline uint64_t rtl_apu_clock_now(const RtlApuFrameClock *clock,\n                                        uint64_t master) {\n  /* RESET may initialize CPU state inside the first host iteration. */\n  uint64_t within = master >= clock->start_master ? master - clock->start_master : 0;\n  return clock->start_guest + within * RTL_APU_CYCLES_PER_FRAME /\n                               RTL_MASTER_CYCLES_PER_FRAME;\n}\n\nstatic inline uint64_t rtl_apu_clock_finish(RtlApuFrameClock *clock,\n                                           uint64_t master) {\n  uint64_t end = rtl_apu_clock_now(clock, master);\n  uint64_t minimum = clock->start_guest + RTL_APU_CYCLES_PER_FRAME;\n  if (end < minimum) end = minimum;  /* WAI still advances a hardware frame. */\n  clock->last_duration = end - clock->start_guest;\n  clock->next_guest = end;\n  /* Leave the current origin intact: raster IRQs can still touch APU ports\n   * between the completed game iteration and the next clock_begin. */\n  return end;\n}\n'

# Verbatim common_rtl.c regions the correction replaces, joined by filler.
PINNED_RTL = "\n/* ... */\n".join(('  return g_extended_frame_timing && g_apu_frame_clock.last_duration\n      ? (double)g_apu_frame_clock.last_duration / RTL_APU_CYCLES_PER_FRAME : 1.0;\n', '  return (uint64_t)snes_frame_counter * RTL_APU_CYCLES_PER_FRAME +\n         within * RTL_APU_CYCLES_PER_FRAME /\n             RTL_MASTER_CYCLES_PER_FRAME;\n', '      : (uint64_t)snes_frame_counter * RTL_APU_CYCLES_PER_FRAME;\n'))

FIELD = 357368
DRIVER = r"""
#include <stdio.h>
#include <stdlib.h>
#include "apu_frame_clock.h"
int main(int argc, char **argv) {
  int fields = atoi(argv[1]);
  RtlApuFrameClock c = {0};
  uint64_t master = 1000, total = 0;
  for (int i = 0; i < fields; i++) {
    rtl_apu_clock_begin(&c, master);
    /* A short (WAI) iteration still spans one field. */
    master += (i % 7 == 3) ? 1000 : FIELD_LEN;
    uint64_t end = rtl_apu_clock_finish(&c, master);
    total += c.last_duration;
    if (end != total) return 2;
  }
  printf("%llu\n", (unsigned long long)total);
  return 0;
}
"""


class PatchTest(unittest.TestCase):
    def test_pinned_header_is_the_recognized_revision(self):
        digest = hashlib.sha256(PINNED_HEADER.encode("utf-8")).hexdigest()
        self.assertEqual(digest, fix.PINNED_HEADER_SHA256)

    def test_corrects_header_and_rtl_once(self):
        header = fix.patch_header(PINNED_HEADER)
        self.assertEqual(header, fix.CORRECTED_HEADER)
        self.assertEqual(fix.patch_header(header), header)
        rtl = fix.patch_rtl(PINNED_RTL)
        self.assertEqual(rtl.count(fix.MARK), 3)
        self.assertNotIn("* RTL_APU_CYCLES_PER_FRAME", rtl)
        self.assertEqual(fix.patch_rtl(rtl), rtl)

    def test_rejects_unknown_revision_and_tampering(self):
        with self.assertRaisesRegex(ValueError, "not recognized"):
            fix.patch_header(PINNED_HEADER.replace("17088ull", "17089ull"))
        with self.assertRaisesRegex(ValueError, "not recognized"):
            fix.patch_rtl(PINNED_RTL.replace("RTL_APU_CYCLES_PER_FRAME /", "X /"))
        with self.assertRaisesRegex(ValueError, "altered"):
            fix.patch_header(fix.CORRECTED_HEADER + "\n")


@unittest.skipUnless(shutil.which("cc") or shutil.which("gcc"), "needs a C compiler")
class ReferenceRateTest(unittest.TestCase):
    def run_clock(self, header, fields):
        cc = shutil.which("cc") or shutil.which("gcc")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "apu_frame_clock.h").write_text(header)
            (tmp / "t.c").write_text(DRIVER)
            exe = tmp / "t"
            subprocess.run([cc, "-std=c99", "-O2", "-Wall", "-Werror", f"-DFIELD_LEN={FIELD}ull",
                            f"-I{tmp}", str(tmp / "t.c"), "-o", str(exe)], check=True)
            out = subprocess.run([str(exe), str(fields)], check=True,
                                 capture_output=True, text=True).stdout
        return int(out)

    def test_pinned_clock_is_17088_per_field(self):
        self.assertEqual(self.run_clock(PINNED_HEADER, 600), 600 * 17088)

    def test_corrected_clock_matches_snes9x_ratio_without_drift(self):
        # Snes9x APU_NUMERATOR_NTSC / APU_DENOMINATOR_NTSC per master clock.
        self.assertEqual(self.run_clock(fix.CORRECTED_HEADER, 600),
                         600 * FIELD * 15664 // 328125)
        self.assertEqual(self.run_clock(fix.CORRECTED_HEADER, 36000),
                         36000 * FIELD * 15664 // 328125)


if __name__ == "__main__":
    unittest.main()
