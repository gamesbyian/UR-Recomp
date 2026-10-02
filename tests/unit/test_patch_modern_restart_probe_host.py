import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "patch_modern_restart_probe_host.py"

spec = importlib.util.spec_from_file_location("restart_probe_patcher", TOOL)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class RestartProbeHostPatchTests(unittest.TestCase):
    def test_injects_only_title_hooks_and_probe(self):
        source = """#include "host_main.h"
#include "game_rtl.h"
#include "snesrecomp_rom_identity.h"  /* generated from rom_identity.txt */

static const SnesDesktopHostGame kGameHost = {
    .display_name        = "Uniracers",
    .game_info           = &kGameInfo,
    .num_players         = 2,
};
"""
        patched = mod.patch_text(source)
        self.assertIn('#include "common_rtl.h"', patched)
        self.assertIn("g_ram[0x0313] == 1", patched)
        self.assertIn("RtlRollbackSaveToMemory", patched)
        self.assertIn("RtlRollbackSnapshotBound", patched)
        self.assertIn("RtlRollbackLoadFromMemory", patched)
        self.assertNotIn(".before_run_frame", patched)
        self.assertIn(".after_run_frame", patched)
        self.assertIn("UR_RESTART_PROBE %s replay_equal=%d window=%u", patched)
        self.assertIn('ok ? "PASS" : "FAIL"', patched)

    def test_idempotent(self):
        source = """#include "host_main.h"
#include "game_rtl.h"
#include "snesrecomp_rom_identity.h"  /* generated from rom_identity.txt */

static const SnesDesktopHostGame kGameHost = {
    .game_info           = &kGameInfo,
};
"""
        once = mod.patch_text(source)
        self.assertEqual(mod.patch_text(once), once)

    def test_fails_closed_on_unknown_template(self):
        with self.assertRaises(ValueError):
            mod.patch_text("int main(void) { return 0; }\n")


if __name__ == "__main__":
    unittest.main()
