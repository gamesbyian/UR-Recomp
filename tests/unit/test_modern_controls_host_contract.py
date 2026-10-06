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
        continue_shortcut = body.index("key == SDLK_F3")
        self.assertLess(controls, help_shortcut)
        self.assertLess(controls, continue_shortcut)
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

        self.assertIn("!g_controls_visible", body)
        self.assertIn("modern_controls_action_for_snes_control", body)
        self.assertIn("handle_controls_action(action)", body)
        self.assertIn("UR_CONTROLS CAPTURE_CANCELLED", body)

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
