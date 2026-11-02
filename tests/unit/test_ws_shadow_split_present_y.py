"""Compile the actual pinned ws_shadow patch accessors and test split Y phase.

This is a bounded source-level regression, not original/native pixel acceptance.
The production PPU combines PresentWorldY with (sy - ScrollY) & 0x3ff.
Those accessors must select the same viewport origin in retained-history mode.
"""

from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "tools/patches/snesrecomp-ws-shadow-split-band.patch"


def patched_source_lines():
    """Read the post-patch lines of the pinned ws_shadow.c hunks."""
    in_source = False
    for line in PATCH.read_text(encoding="utf-8").splitlines():
        if line.startswith("+++ b/"):
            in_source = line == "+++ b/runner/src/snes/ws_shadow.c"
            continue
        if in_source and line.startswith((" ", "+")) and not line.startswith("+++ "):
            yield line[1:]


def extract_function(name):
    lines = list(patched_source_lines())
    start = next(i for i, line in enumerate(lines)
                 if re.search(r"\b" + re.escape(name) + r"\(", line) and "{" in line)
    body = []
    depth = 0
    opened = False
    for line in lines[start:]:
        body.append(line)
        depth += line.count("{") - line.count("}")
        opened |= "{" in line
        if opened and depth == 0:
            return "\n".join(body) + "\n"
    raise AssertionError(f"incomplete pinned patch function: {name}")


class SplitPresentationYTests(unittest.TestCase):
    def test_pinned_accessors_preserve_each_viewports_vertical_phase(self):
        compiler = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
        if compiler is None:
            self.skipTest("C compiler unavailable")
        functions = "\n".join(extract_function(name) for name in (
            "UseSplit", "WsShadowPresentWorldY", "WsShadowScrollY"))
        program = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#define kLayers 2

typedef struct {
  bool splitActive;
  bool retainHistory;
  int splitLine;
  uint32_t scrollY, splitScrollY, worldY, splitWorldY;
} WsShadowLayer;
static WsShadowLayer s_layers[kLayers];
static int s_currentLine;
''' + functions + r'''
int main(void) {
  WsShadowLayer *layer = &s_layers[0];
  layer->splitActive = true;
  layer->splitLine = 113;
  layer->scrollY = 3;
  layer->splitScrollY = 11;
  layer->worldY = 80;
  layer->splitWorldY = 97;
  layer->retainHistory = true;

  s_currentLine = 112;
  assert(WsShadowPresentWorldY(0, 0) == 3);
  assert(WsShadowScrollY(0) == 3);
  s_currentLine = 113;
  assert(WsShadowPresentWorldY(0, 0) == 11);
  assert(WsShadowScrollY(0) == 11);
  /* Exact PPU calculation: pixel Y phase must follow lower viewport's
   * scroll, not top viewport's unrelated fine-scroll phase. */
  const uint32_t sy = 43;
  const uint32_t py = WsShadowPresentWorldY(0, 0) +
      ((sy - WsShadowScrollY(0)) & 0x3ffu);
  assert((py & 15u) == (sy & 15u));

  layer->retainHistory = false;
  assert(WsShadowPresentWorldY(0, 0) == 97);
  s_currentLine = 112;
  assert(WsShadowPresentWorldY(0, 0) == 80);
  layer->splitActive = false;
  s_currentLine = 113;
  layer->retainHistory = true;
  assert(WsShadowPresentWorldY(0, 0) == 3);
  assert(WsShadowScrollY(0) == 3);
  assert(WsShadowPresentWorldY(-1, 0) == 0);
  assert(WsShadowScrollY(kLayers) == 0);
  return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "split_y.c"
            exe = Path(tmp) / "split_y"
            src.write_text(program, encoding="utf-8")
            subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                            str(src), "-o", str(exe)], check=True)
            subprocess.run([str(exe)], check=True)


if __name__ == "__main__":
    unittest.main()
