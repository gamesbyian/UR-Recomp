import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
WRAPPER = ROOT / "native" / "product" / "completed_run_browser_host.cpp"
PATCHER = ROOT / "tools" / "patch_modern_product_host.py"
GAMEPAD_PATCH = ROOT / "tools" / "patches" / "snesrecomp-title-gamepad-hook.patch"


class ModernControlsHostContractTests(unittest.TestCase):
    def test_keyboard_controls_modal_precedes_global_shortcuts(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index('extern "C" int ur_uniracers_modern_system_key_down(')
        end = source.index(
            'extern "C" int ur_uniracers_modern_system_gamepad_button(', start)
        body = source[start:end]

        controls = body.index("if (g_controls_visible)")
        help_shortcut = body.index("key == SDLK_F1")
        tour_shortcut = body.index(
            "if (modern_mode() && key == SDLK_F3 && !paused()"
        )
        self.assertLess(controls, help_shortcut)
        self.assertLess(controls, tour_shortcut)
        self.assertIn("return handle_controls_key(key) ? 1 : 0;", body)

    def test_raw_controls_gamepad_path_defers_to_framework_mapping(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index(
            'extern "C" int ur_uniracers_modern_system_gamepad_button(')
        end = source.index(
            'extern "C" int ur_uniracers_modern_system_gamepad_control(', start)
        body = source[start:end]

        controls = body.index("if (g_controls_visible)")
        generic_release = body.index(
            "if (!pressed) {\n"
            "        if (button == g_practice_cancel_gamepad_button)"
        )
        controls_block = body[controls:controls + 520]
        self.assertLess(controls, generic_release)
        self.assertIn("mapped P1 semantics only", controls_block)
        self.assertIn("return -1;", controls_block)

    def test_failed_restart_retirement_aborts_through_rollback(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index(
            "if (retire_tour_continuation_after_stock_reset())"
        )
        end = source.index(
            "if (current->rider_index == saved.rider_index", start
        )
        body = source[start:end]
        self.assertIn(
            'abort_tour_continue(\n'
            '                        "UR_TOUR_RESTART RETIRE_PERSIST_FAILED")',
            body,
        )
        self.assertNotIn("Keep Ready", body)

    def test_restart_retirement_publishes_profile_before_sram(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index("bool retire_tour_continuation_after_stock_reset()")
        end = source.index("bool save_active_profile_state(", start)
        body = source[start:end]

        profile_save = body.index("save_host_profile_state_file(")
        sram_save = body.index("RtlTryWriteSram()")
        rollback = body.index("UR_TOUR_RESTART PROFILE_ROLLED_BACK")
        self.assertLess(profile_save, sram_save)
        self.assertLess(sram_save, rollback)
        self.assertIn("candidate.tour_continuation.reset()", body)
        self.assertIn("g_profile_state = std::move(candidate);", body)

    def test_tour_route_uses_semantic_race_surface(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index("void advance_tour_continue_route(uint64_t next_frame)")
        end = source.index("bool retire_tour_continuation_after_stock_reset()", start)
        body = source[start:end]

        self.assertIn(
            "g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE",
            body,
        )
        self.assertNotIn(
            "g_ram[0x0313] == 0x01",
            body,
        )

    def test_explicit_tour_route_suppresses_passive_resume_until_ready(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index("void reconcile_tour_resume()")
        end = source.index("bool restart_surface()", start)
        body = source[start:end]

        ownership = body.index(
            "g_tour_continue.stage !=\n"
            "            ur::product::ModernTourContinueStage::Idle"
        )
        passive = body.index(
            "// Passive stock arrival at TRACK_SELECT"
        )
        self.assertLess(ownership, passive)
        self.assertIn(
            "ModernTourContinueStage::Ready",
            body[ownership:ownership + 400],
        )

    def test_tour_wipe_detection_uses_title_owned_empty_row_evidence(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index("bool tour_entry_crossed_stock_rider_wipe()")
        end = source.index(
            "bool rollback_tour_entry_to_profile_snapshot()", start
        )
        body = source[start:end]
        self.assertIn("tour_qualification_row_empty(", body)
        self.assertIn("g_profile_state->tour_continuation", body)

    def test_tour_terminal_failures_preserve_pre_step_wipe_state(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index("void advance_tour_continue_route(uint64_t next_frame)")
        end = source.index("void reconcile_tour_resume()", start)
        body = source[start:end]

        crossed = body.index(
            "const bool crossed_stock_rider_wipe =\n"
            "        tour_entry_crossed_stock_rider_wipe();"
        )
        advance = body.index("advance_modern_tour_continue(")
        timeout = body.index("ABORTED_TIMEOUT")
        unexpected = body.index("ABORTED_UNEXPECTED_RACE")
        self.assertLess(crossed, advance)
        self.assertIn("crossed_stock_rider_wipe", body[timeout:timeout + 180])
        unexpected_abort = body.index(
            "abort_tour_continue(", unexpected
        )
        self.assertIn(
            "crossed_stock_rider_wipe",
            body[unexpected_abort:unexpected_abort + 220],
        )

    def test_tour_controller_shortcut_is_semantic_end_to_end(self):
        source = HOST.read_text(encoding="utf-8")
        raw_start = source.index(
            'extern "C" int ur_uniracers_modern_system_gamepad_button(')
        raw_end = source.index(
            'extern "C" int ur_uniracers_modern_system_gamepad_control(',
            raw_start,
        )
        raw = source[raw_start:raw_end]
        semantic_start = raw_end
        semantic_end = source.index(
            'extern "C" void ur_uniracers_modern_system_overlay(',
            semantic_start,
        )
        semantic = source[semantic_start:semantic_end]

        self.assertNotIn(
            "button == kGamepadBtn_Y &&\n"
            "             (tour_continue_available()",
            raw,
        )
        self.assertIn(
            "pressed && control == 9",
            semantic,
        )
        self.assertIn("open_tour_action_menu()", semantic)

    def test_framework_bookkeeps_gamepad_edge_before_title_callback(self):
        source = GAMEPAD_PATCH.read_text(encoding="utf-8")
        bookkeeping = source.index("gi->modifiers ^= 1 << button;")
        callback = source.index("g_game->system_gamepad_button(button, pressed)")
        semantic = source.index("g_game->system_gamepad_control(")
        dispatch = source.index("SetPadButtonOrFallthrough")

        self.assertLess(bookkeeping, callback)
        self.assertLess(callback, semantic)
        self.assertLess(semantic, dispatch)

    def test_semantic_controls_path_uses_tested_policy(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index(
            'extern "C" int ur_uniracers_modern_system_gamepad_control(')
        end = source.index(
            'extern "C" void ur_uniracers_modern_system_overlay(', start)
        body = source[start:end]

        controls = body.index("if (g_controls_visible)")
        regional = body.index("RegionalControllerAction regional_action")
        self.assertLess(controls, regional)
        self.assertIn("modern_controls_action_for_snes_control", body)
        self.assertIn("handle_controls_action(action)", body)
        self.assertIn("UR_CONTROLS CAPTURE_CANCELLED", body)
        self.assertIn("return 1;", body[controls:regional])

    def test_controls_precede_paused_records_gamepad_shortcuts(self):
        source = WRAPPER.read_text(encoding="utf-8")
        start = source.index(
            'extern "C" int ur_uniracers_product_system_gamepad_button(')
        end = source.index(
            'extern "C" int ur_uniracers_product_system_gamepad_control(', start)
        body = source[start:end]

        controls = body.index("ur_uniracers_modern_controls_active()")
        records_y = body.index("pressed && button == kGamepadBtn_Y")
        run_data_x = body.index("pressed && button == kGamepadBtn_X")
        self.assertLess(controls, records_y)
        self.assertLess(controls, run_data_x)
        self.assertIn(
            "return ur_uniracers_modern_system_gamepad_button(button, pressed);",
            body[controls:controls + 320],
        )

    def test_product_wrapper_forwards_semantic_controls(self):
        source = WRAPPER.read_text(encoding="utf-8")
        start = source.index(
            'extern "C" int ur_uniracers_product_system_gamepad_control(')
        end = source.index(
            'extern "C" void ur_uniracers_product_system_overlay(', start)
        body = source[start:end]

        self.assertIn(
            "return ur_uniracers_modern_system_gamepad_control(control, pressed);",
            body,
        )

    def test_generated_host_binds_raw_and_semantic_callbacks(self):
        source = PATCHER.read_text(encoding="utf-8")
        self.assertIn(
            ".system_gamepad_button = &ur_uniracers_product_system_gamepad_button",
            source,
        )
        self.assertIn(
            ".system_gamepad_control = &ur_uniracers_product_system_gamepad_control",
            source,
        )


if __name__ == "__main__":
    unittest.main()
