import tempfile
import unittest
from pathlib import Path

from tools.patch_widescreen_probe_host import patch_host


class WidescreenProbeHostPatchTests(unittest.TestCase):
    def test_generated_host_gets_only_presentation_hooks(self):
        source = """#include "host_main.h"
#include "game_rtl.h"

static const SnesDesktopHostGame kGameHost = {
    .display_name = "Uniracers",
    .num_players         = 2,
};
"""
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "main.c"
            path.write_text(source, encoding="utf-8")
            patch_host(path)
            out = path.read_text(encoding="utf-8")

        self.assertIn('#include "snes/ppu.h"', out)
        self.assertIn("WidescreenProbePrepareFrame", out)
        self.assertIn(".native_widescreen    = 1,", out)
        self.assertIn(".prepare_frame        = WidescreenProbePrepareFrame,", out)
        self.assertIn("PpuWsExtraOverride()", out)
        self.assertIn("*frame_w = 256 + extra * 2;", out)
        self.assertNotIn("g_ram", out)
        self.assertNotIn("poke", out.lower())


if __name__ == "__main__":
    unittest.main()
