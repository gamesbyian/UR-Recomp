import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
PATCH = ROOT / "tools" / "patches" / "snesrecomp-source-gamepad-hook.patch"
PATCHER = ROOT / "tools" / "patch_modern_product_host.py"


class LocalMultiplayerHostContractTests(unittest.TestCase):
    def test_framework_patch_is_syntactically_valid(self):
        result = subprocess.run(
            ["git", "apply", "--numstat", str(PATCH)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_framework_source_hook_precedes_ordinary_title_dispatch(self):
        source = PATCH.read_text(encoding="utf-8")
        source_callback = source.index("g_game->system_gamepad_source_button(")
        consume_return = source.index("    return;", source_callback)
        bookkeeping = source.index("Keep per-controller physical/modifier bookkeeping", source_callback)
        self.assertLess(source_callback, consume_return)
        self.assertLess(consume_return, bookkeeping)
        self.assertIn("system_gamepad_source_connection", source)

    def test_modern_join_is_contextual_to_stock_two_player_select(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn("g_ram[0x009F] == 0x3D", source)
        self.assertIn("has_controller_source", source)
        self.assertIn("source.connected", source)
        self.assertIn("UR_LOCAL_MULTIPLAYER STOCK_FALLBACK_NO_CONTROLLER", source)
        self.assertIn("UR_LOCAL_MULTIPLAYER JOIN_OPENED", source)
        self.assertIn("UR_LOCAL_MULTIPLAYER SESSION_READY", source)
        self.assertIn("UR_LOCAL_MULTIPLAYER STOCK_FALLBACK", source)
        self.assertIn("UR_LOCAL_MULTIPLAYER STOCK_FALLBACK_NO_PROFILES", source)
        self.assertIn("local_multiplayer_slot_label(slot)", source)
        self.assertIn("local_multiplayer_participant_row_text(", source)
        self.assertIn("PICK MATCHING STOCK RIDERS", source)
        self.assertIn("local_multiplayer_participants_ready", source)
        self.assertIn("g_local_multiplayer_participants_ready", source)
        self.assertIn("local_multiplayer_confirm_profile", source)
        self.assertIn("local_multiplayer_profile_candidate", source)

    def test_source_button_assigns_framework_seat_and_consumes_modal_edges(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index(
            'extern "C" int ur_uniracers_modern_system_gamepad_source_button(')
        end = source.index(
            'extern "C" int ur_uniracers_modern_system_gamepad_button(', start)
        body = source[start:end]
        self.assertIn("local_multiplayer_slot_for_player(player_index)", body)
        self.assertIn("button == kGamepadBtn_A || button == kGamepadBtn_Start", body)
        self.assertIn("local_multiplayer_assign_source(slot, source)", body)
        self.assertIn("local_multiplayer_confirm_profile(slot)", body)
        self.assertIn("local_multiplayer_move_profile(", body)
        self.assertIn("local_multiplayer_clear_profile(", body)
        self.assertIn("g_local_multiplayer_consumed_buttons", body)
        self.assertIn("g_local_multiplayer_consumed_buttons[seat] &= ~button_bit;", body)
        self.assertIn("button == kGamepadBtn_B", body)
        self.assertIn("button == kGamepadBtn_DpadLeft", body)
        self.assertIn("button == kGamepadBtn_DpadRight", body)

    def test_generated_host_binds_source_callbacks(self):
        source = PATCHER.read_text(encoding="utf-8")
        self.assertIn(
            ".system_gamepad_source_button = &ur_uniracers_modern_system_gamepad_source_button",
            source,
        )
        self.assertIn(
            ".system_gamepad_source_connection = &ur_uniracers_modern_system_gamepad_source_connection",
            source,
        )


if __name__ == "__main__":
    unittest.main()
