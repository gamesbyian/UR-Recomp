import unittest

from tools.apply_native_racer_presentation_probe import CMAKE_BLOCK, PROBE_CPP, patch_cmake, patch_main


class NativeRacerPresentationProbePatchTests(unittest.TestCase):
    def test_main_patch_is_idempotent(self):
        source = (
            '#include "snesrecomp_rom_identity.h"  /* generated from rom_identity.txt */\n'
            'static const SnesDesktopHostGame kGameHost = {\n'
            '    .game_info           = &kGameInfo,\n'
            '};\n'
        )
        patched = patch_main(source)
        self.assertIn("UrRacerPresentationProbeAfterRunFrame", patched)
        self.assertIn(".after_run_frame", patched)
        self.assertEqual(patch_main(patched), patched)

    def test_cmake_patch_targets_generated_game(self):
        source = "snesrecomp_target_desktop_host(UniracersSNESRecomp)\n"
        patched = patch_cmake(source)
        self.assertIn("racer_replacement_selector.cpp", patched)
        self.assertIn("racer_guest_snapshot.cpp", patched)
        self.assertIn("ur_racer_presentation_probe.cpp", patched)
        self.assertIn("UR_RECOMP_SOURCE_ROOT", CMAKE_BLOCK)
        self.assertEqual(patch_cmake(patched), patched)

    def test_probe_is_observer_only(self):
        body = PROBE_CPP.replace("extern std::uint8_t g_ram[0x20000];", "")
        self.assertIn("select_racer_presentation_from_wram", PROBE_CPP)
        self.assertNotIn("g_ram[", body)
        self.assertNotIn("memcpy", PROBE_CPP)
        self.assertNotIn("RtlPoke", PROBE_CPP)
        self.assertNotIn("RtlWrite", PROBE_CPP)


if __name__ == "__main__":
    unittest.main()
