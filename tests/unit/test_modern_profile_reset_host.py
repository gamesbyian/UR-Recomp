import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = (ROOT / "native" / "product" / "uniracers_modern_host.cpp").read_text()


class ModernProfileResetHostContractTests(unittest.TestCase):
    def test_reset_reuses_clean_stock_sram_and_preserves_racer_identity(self):
        self.assertIn("auto reset_sram = ur::product::clean_stock_sram();", HOST)
        self.assertIn(
            "reset_sram[0x0748] = g_profile_state->racer_identity->rider_index;",
            HOST,
        )
        self.assertIn("candidate.tour_continuation.reset();", HOST)
        self.assertIn(
            "capture_stock_sram_for_profile(\n"
            "            ur::product::ExecutionMode::Modern,\n"
            "            candidate,\n"
            "            reset_sram.data(),",
            HOST,
        )

    def test_reset_is_transactional_across_profile_metadata_and_sram(self):
        fn_start = HOST.index("bool execute_active_profile_progress_reset()")
        fn_end = HOST.index("\nvoid open_profile_reset_confirmation()", fn_start)
        body = HOST[fn_start:fn_end]

        profile_save = body.index("save_host_profile_state_file(")
        install_live = body.index("std::memcpy(g_sram, reset_sram.data()")
        sram_save = body.index("RtlTryWriteSram()", install_live)
        rollback_live = body.index(
            "std::memcpy(g_sram, original_sram.data()", sram_save
        )
        rollback_profile = body.index(
            "save_host_profile_state_file(", rollback_live
        )

        self.assertLess(profile_save, install_live)
        self.assertLess(install_live, sram_save)
        self.assertLess(sram_save, rollback_live)
        self.assertLess(rollback_live, rollback_profile)
        self.assertIn("UR_PROFILE_RESET ROLLED_BACK", body)

    def test_reset_requires_modern_authoritative_active_profile(self):
        self.assertIn("active_profile_reset_authoritative()", HOST)
        self.assertIn("selected_profile_is_active()", HOST)
        self.assertIn("ModernProfileResetAction::Execute", HOST)
        self.assertIn("D/PAD Y RESET PROGRESS", HOST)
        self.assertIn("RESET %s PROGRESS?", HOST)

    def test_stock_erase_chord_uses_final_human_input_filter(self):
        fn_start = HOST.index(
            'extern "C" uint32_t ur_uniracers_modern_filter_player_input'
        )
        fn_end = HOST.index(
            '\nextern "C" void ur_uniracers_modern_system_overlay', fn_start
        )
        body = HOST[fn_start:fn_end]
        self.assertIn("g_ram[0x009F] == 0xD7", body)
        self.assertIn("g_ram[0x0313] != 0x01", body)
        self.assertIn("modern_profile_admin_filter_human_input(", body)
        self.assertIn("ExecutionMode::Modern", body)
        self.assertIn("ExecutionMode::Authentic", body)



if __name__ == "__main__":
    unittest.main()
