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
    def test_injects_product_command_path_and_probe(self):
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
        self.assertIn('#include "modern_session_c_api.h"', patched)
        self.assertIn("g_ram[0x0313] == 1", patched)
        self.assertIn("ur_modern_session_observe_race_active", patched)
        self.assertIn("ur_modern_session_restart_race", patched)
        self.assertIn("RtlRollbackSaveToMemory", patched)
        self.assertIn("RtlRollbackSnapshotBound", patched)
        self.assertIn("RtlRollbackLoadFromMemory", patched)
        self.assertIn("RtlSetRewindAudioTimingLock", patched)
        self.assertIn("RtlAudioSetFastForward(true)", patched)
        self.assertIn("RtlAudioSetFastForward(false)", patched)
        self.assertIn("sram_progression_unchanged=1", patched)
        self.assertIn('#include "netplay/snes_state_digest.h"', patched)
        self.assertIn("snes_state_digest_parts", patched)
        self.assertIn("snes_state_digest_first_diff", patched)
        self.assertNotIn(".before_run_frame", patched)
        self.assertIn(".after_run_frame", patched)
        self.assertIn("UR_RESTART_PROBE PASS command_dispatch=1", patched)
        self.assertIn("repeated_restart_equal=1", patched)
        self.assertNotIn(r";\nstatic", patched)

    def test_links_product_runtime_and_digest_into_generated_target(self):
        cmake = """cmake_minimum_required(VERSION 3.20)
project(UniracersSNESRecomp C CXX)
add_executable(UniracersSNESRecomp
    src/main.c
)
"""
        product_root = pathlib.Path("/tmp/ur-recomp")
        patched = mod.patch_cmake_text(cmake, product_root)
        self.assertIn(
            'target_include_directories(UniracersSNESRecomp PRIVATE '
            '"/tmp/ur-recomp/native/product")',
            patched,
        )
        for name in (
            "session_control.cpp",
            "session_runtime_adapter.cpp",
            "race_restart_anchor.cpp",
            "race_restart_lifecycle.cpp",
            "modern_session_runtime.cpp",
            "modern_session_c_api.cpp",
        ):
            self.assertIn(name, patched)
        self.assertIn(
            '"${SNESRECOMP_ROOT}/runner/src/netplay/snes_state_digest.c"',
            patched,
        )
        self.assertEqual(mod.patch_cmake_text(patched, product_root), patched)

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
