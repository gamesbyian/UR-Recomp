import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_spc_frame_clock_patch as fix  # noqa: E402
import baldosa_spc_reference_rate_patch as rate  # noqa: E402

FIELD = 357368
# Prints the SPC timeline (master clocks) after N host iterations whose CPU
# spans alternate around a field: 357,368 +/- 500, with every 7th iteration
# 1,000 clocks (a WAI-short one, the case the pinned clamp inflated).
DRIVER = r"""
#include <stdio.h>
#include <stdlib.h>
#include "apu_frame_clock.h"
int main(int argc, char **argv) {
  int iters = atoi(argv[1]);
  RtlApuFrameClock c = {0};
  uint64_t master = 1000, cpu = 0;
  for (int i = 0; i < iters; i++) {
    rtl_apu_clock_begin(&c, master);
    uint64_t span = (i % 7 == 3) ? 1000 : (i & 1 ? FIELD_LEN + 500 : FIELD_LEN - 500);
    if (i % 7 == 4) span = 2 * FIELD_LEN - 1000;  /* catch up after the short one */
    if (rtl_apu_clock_timeline(&c, master + span) > c.start_timeline + span) return 3;
    master += span;
    cpu += span;
    rtl_apu_clock_finish(&c, master);
    if (c.next_guest != rtl_apu_cycles_of_master(c.next_timeline)) return 2;
  }
  printf("%llu %llu\n", (unsigned long long)c.next_timeline, (unsigned long long)cpu);
  return 0;
}
"""


class PatchTest(unittest.TestCase):
    def test_stages_once_on_rf016_header(self):
        out = fix.patch(rate.CORRECTED_HEADER)
        self.assertEqual(fix.patch(out), out)
        self.assertNotIn("if (end < minimum) end = minimum;", out)
        self.assertIn("rtl_apu_short_line_pause(clock->field_parity, within)", out)
        self.assertIn(rate.MARK, out)

    def test_requires_rf016_and_rejects_tampering(self):
        with self.assertRaisesRegex(ValueError, "RF-016"):
            fix.patch("#pragma once\n")
        with self.assertRaisesRegex(ValueError, "not recognized"):
            fix.patch(rate.CORRECTED_HEADER.replace("if (end < minimum)", "if (end <= minimum)"))
        with self.assertRaisesRegex(ValueError, "altered"):
            fix.patch(fix.patch(rate.CORRECTED_HEADER).replace("d < 4 ? d : 4", "d"))


@unittest.skipUnless(shutil.which("cc") or shutil.which("gcc"), "needs a C compiler")
class FrameClockTest(unittest.TestCase):
    def run_clock(self, header, iters):
        cc = shutil.which("cc") or shutil.which("gcc")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "apu_frame_clock.h").write_text(header)
            (tmp / "t.c").write_text(DRIVER)
            exe = tmp / "t"
            subprocess.run([cc, "-std=c99", "-O2", "-Wall", "-Werror", f"-DFIELD_LEN={FIELD}ull",
                            f"-I{tmp}", str(tmp / "t.c"), "-o", str(exe)], check=True)
            res = subprocess.run([str(exe), str(iters)], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        timeline, cpu = map(int, res.stdout.split())
        return timeline, cpu

    def test_rf016_clamp_inflates_spc_time(self):
        timeline, cpu = self.run_clock(rate.CORRECTED_HEADER, 700)
        self.assertGreater(timeline, cpu)

    def test_timeline_is_cpu_time_less_four_clocks_per_odd_field(self):
        timeline, cpu = self.run_clock(fix.patch(rate.CORRECTED_HEADER), 700)
        fields = cpu // FIELD
        self.assertEqual(cpu % FIELD, 0)
        self.assertEqual(cpu - timeline, 4 * (fields // 2))


if __name__ == "__main__":
    unittest.main()
