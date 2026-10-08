import unittest

from tools.apply_native_racer_presentation_probe import CMAKE_BLOCK, PROBE_CPP, patch_cmake, patch_main


class NativeRacerPresentationProbePatchTests(unittest.TestCase):
    def test_main_patch_is_idempotent(self):
        source = (
            '#include "snesrecomp_rom_identity.h"  /* generated from rom_identity.txt */\n'
            'static const SnesDesktopHostGame kGameHost = {\n'
            '    .game_info           = &kGameInfo,\n'
            '};\n'
            'int main(int argc, char **argv) {\n'
            '    return snesrecomp_desktop_main(&kGameHost, argc, argv);\n'
            '}\n'
        )
        patched = patch_main(source)
        self.assertIn("UrRacerPresentationProbeAfterRunFrame", patched)
        self.assertIn(".after_run_frame", patched)
        self.assertIn(".prepare_frame", patched)
        self.assertIn(".begin_sim_frame", patched)
        self.assertIn(".draw_frame", patched)
        self.assertIn(".presentation_scale", patched)
        self.assertIn("static SnesDesktopHostGame kGameHost = {", patched)
        self.assertIn("kGameHost.native_widescreen = UrRacerHdProbeWideRequested() != 0;", patched)
        self.assertNotIn(".native_widescreen   = 1,", patched)

        self.assertEqual(patch_main(patched), patched)

    def test_cmake_patch_targets_generated_game(self):
        source = "snesrecomp_target_desktop_host(UniracersSNESRecomp)\n"
        patched = patch_cmake(source)
        self.assertIn("racer_replacement_selector.cpp", patched)
        self.assertIn("racer_guest_snapshot.cpp", patched)
        self.assertIn("racer_oam_placement.cpp", patched)
        self.assertIn("racer_hd_presenter.cpp", patched)
        self.assertIn("ur_racer_presentation_probe.cpp", patched)
        self.assertIn("UR_RECOMP_SOURCE_ROOT", CMAKE_BLOCK)
        self.assertEqual(patch_cmake(patched), patched)

    def test_probe_keeps_guest_state_read_only(self):
        body = PROBE_CPP.replace("extern std::uint8_t g_ram[0x20000];", "")
        self.assertIn("select_racer_presentation_from_wram", PROBE_CPP)
        self.assertIn("racer_hd_draw_frame", PROBE_CPP)
        self.assertIn("racer_hd_presentation_scale", PROBE_CPP)
        self.assertIn("UR_RACER_HD_PROBE_WIDE", PROBE_CPP)
        self.assertIn("snesrecomp_desktop_frame_width", PROBE_CPP)
        self.assertIn("overlayCaptures[kPpuOverlaySource_Obj]", PROBE_CPP)
        self.assertIn("UR_RACER_HD_WIDE_CAPTURE PASS", PROBE_CPP)
        self.assertIn("UR_RACER_HD_P1_NATIVE_TEST", PROBE_CPP)
        self.assertIn("UR_RACER_HD_P1_NATIVE_SUMMARY", PROBE_CPP)
        self.assertIn("UR_RACER_HD_P1_DIAGNOSTIC frame=", PROBE_CPP)
        self.assertIn("singleton_candidates=%u", PROBE_CPP)
        self.assertIn("split_small_alias=%u", PROBE_CPP)
        self.assertIn("bottom_overlap=%u", PROBE_CPP)
        self.assertIn("geometry_accepted=%u", PROBE_CPP)
        self.assertIn("UR_RACER_HD_P1_NATIVE PASS", PROBE_CPP)
        self.assertIn("p2_stock_roi_exact=1", PROBE_CPP)
        self.assertIn("decode_racer_split_ppu_placement", PROBE_CPP)
        self.assertIn("std::memcmp(src, out, 4)", PROBE_CPP)
        self.assertIn("std::abort()", PROBE_CPP)
        self.assertIn("UR_RACER_PRESENTATION_TRACE", PROBE_CPP)
        self.assertIn("frame >= 1180u && frame <= 1620u", PROBE_CPP)
        self.assertNotIn("if (passed) return;", PROBE_CPP)
        self.assertIn("if (passed || !selection.uses_replacement()) return;", PROBE_CPP)
        self.assertNotIn("g_ram[", body)
        self.assertNotIn("memcpy", PROBE_CPP)
        self.assertNotIn("RtlPoke", PROBE_CPP)
        self.assertNotIn("RtlWrite", PROBE_CPP)


if __name__ == "__main__":
    unittest.main()
