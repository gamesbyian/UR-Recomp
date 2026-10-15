import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_dram_refresh_beam_rate_patch as fix  # noqa: E402

# Verbatim baldosa/snesrecomp@075fbe4 runner/src/common_cpu_infra.c:887-909
# (unchanged at upstream ec8a3e7).
PINNED_FUNCTION = """uint64_t g_refresh_charged_upto;
static uint64_t s_refresh_phase;
void snes_refresh_exempt(void) { g_refresh_charged_upto = g_cpu.master_cycles; }
void snes_refresh_charge(void) {
  uint64_t m = g_cpu.master_cycles;
  if (g_refresh_charged_upto == 0 || m < g_refresh_charged_upto) {
    g_refresh_charged_upto = m;
    return;
  }
  uint64_t delta = m - g_refresh_charged_upto;
  s_refresh_phase += delta;
  uint64_t lines = s_refresh_phase / 1364u;
  if (lines > 4096u) {            /* teleport, not execution */
    s_refresh_phase = 0;
    g_refresh_charged_upto = m;
    return;
  }
  if (lines) {
    s_refresh_phase -= lines * 1364u;
    g_cpu.master_cycles += 40u * lines;
  }
  g_refresh_charged_upto = g_cpu.master_cycles;
}
"""

# One two-byte iteration of original USA 82:B1F2..B202 (with its 82:B293
# callee) as the pinned generated code charges it per block, MEMSEL=0. The
# per-block totals equal Snes9x's executed per-instruction costs (470 clocks).
B1D8_ITERATION_BLOCKS = (46, 68, 58, 84, 68, 58, 88)
FIELD = 262 * 1364

HARNESS = r"""
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
struct { uint64_t master_cycles; } g_cpu;
%s
int main(int argc, char **argv) {
  static const uint64_t blocks[] = {%s};
  const uint64_t fields = strtoull(argv[1], 0, 10);
  const uint64_t end = (uint64_t)%d * fields;
  uint64_t executed = 0, iterations = 0;
  g_cpu.master_cycles = 1;          /* nonzero watermark origin */
  snes_refresh_exempt();
  for (;;) {
    for (unsigned b = 0; b < sizeof(blocks) / sizeof(blocks[0]); b++) {
      snes_refresh_charge();        /* WatchdogCheck at each block entry */
      if (g_cpu.master_cycles - 1 >= end) goto done;
      g_cpu.master_cycles += blocks[b];
      executed += blocks[b];
    }
    iterations++;
  }
done:
  printf("%%llu %%llu %%llu\n", (unsigned long long)(g_cpu.master_cycles - 1),
         (unsigned long long)executed, (unsigned long long)iterations);
  return 0;
}
"""


class PatchTest(unittest.TestCase):
    def test_corrects_exact_pinned_function_once(self):
        out = fix.patch(PINNED_FUNCTION)
        self.assertIn(fix.MARK, out)
        self.assertIn("  g_refresh_charged_upto = m;\n}\n", out)
        self.assertNotIn("g_refresh_charged_upto = g_cpu.master_cycles;\n}", out)
        self.assertEqual(fix.patch(out), out)

    def test_rejects_unknown_revision(self):
        for bad in (PINNED_FUNCTION.replace("40u * lines", "42u * lines"),
                    PINNED_FUNCTION.replace("uint64_t m = g_cpu.master_cycles;",
                                            "uint64_t now = g_cpu.master_cycles;"),
                    PINNED_FUNCTION + PINNED_FUNCTION,
                    ""):
            with self.assertRaises(ValueError):
                fix.patch(bad)

    def test_rejects_altered_marker(self):
        out = fix.patch(PINNED_FUNCTION).replace("g_refresh_charged_upto = m;",
                                                 "g_refresh_charged_upto = m + 1;")
        with self.assertRaises(ValueError):
            fix.patch(out)


class ShippingBridgeStagingTest(unittest.TestCase):
    def test_windows_bridge_stages_correction_before_build(self):
        wf = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        stage = "python tools/baldosa_dram_refresh_beam_rate_patch.py --game baldosa"
        self.assertEqual(wf.count(stage), 1)
        self.assertLess(wf.index('test "$(git -C baldosa/snesrecomp rev-parse HEAD)" = '
                                 "075fbe4c8e0d97b0013be541795c39cb644a9709"), wf.index(stage))
        self.assertLess(wf.index(stage), wf.index("cmake -S baldosa -B baldosa/build-ur-win"))


class NativeRefreshRateTest(unittest.TestCase):
    """Compile and execute the real pinned/corrected C function."""

    def run_function(self, source: str, fields: int) -> tuple[int, int, int]:
        cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
        if not cc:
            self.skipTest("C compiler unavailable")
        blocks = ", ".join(str(b) for b in B1D8_ITERATION_BLOCKS)
        with tempfile.TemporaryDirectory() as tmp:
            c = Path(tmp) / "refresh.c"
            exe = Path(tmp) / "refresh"
            c.write_text(HARNESS % (source, blocks, FIELD), encoding="utf-8")
            subprocess.run([cc, "-std=c99", "-O2", "-Wall", "-Werror", str(c), "-o", str(exe)],
                           check=True, capture_output=True)
            done = subprocess.run([str(exe), str(fields)], check=True,
                                  capture_output=True, text=True)
        beam, executed, iterations = (int(x) for x in done.stdout.split())
        return beam, executed, iterations

    def test_corrected_function_stalls_once_per_beam_line(self):
        fields = 34
        beam, executed, _ = self.run_function(fix.patch(PINNED_FUNCTION), fields)
        lines = beam // 1364
        stalls = (beam - executed) // 40
        self.assertEqual((beam - executed) % 40, 0)
        self.assertLessEqual(abs(stalls - lines), 1)
        # Hardware leaves the CPU 1324 of every 1364 clocks.
        self.assertLessEqual(abs(executed - 1324 * lines), 1364)

    def test_pinned_function_reproduces_the_rf015_surplus(self):
        fields = 34
        beam, executed, _ = self.run_function(PINNED_FUNCTION, fields)
        stalls = (beam - executed) // 40
        # One stall per 1404 beam clocks: ~1.14 extra CPU clocks per line.
        self.assertLessEqual(abs(stalls - beam // 1404), 1)
        surplus = executed - 1324 * (beam // 1364)
        self.assertGreater(surplus, 8000)   # RF-015: ~9,300 clocks over the phase

    def test_corrected_upload_does_less_work_per_phase(self):
        _, _, pinned = self.run_function(PINNED_FUNCTION, 34)
        _, _, corrected = self.run_function(fix.patch(PINNED_FUNCTION), 34)
        # 470 clocks per two-byte iteration: ~20 iterations (40 VRAM bytes)
        # of upload per 34 fields separate the two rates.
        self.assertGreaterEqual(pinned - corrected, 17)
        self.assertLessEqual(pinned - corrected, 23)


if __name__ == "__main__":
    unittest.main()
