import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


class RegionalPresentationHostContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HOST.read_text(encoding="utf-8")

    def test_keyboard_route_uses_coordinator_before_global_shortcuts(self):
        source = self.source
        start = source.index(
            'extern "C" int ur_uniracers_modern_system_key_down(')
        end = source.index(
            'extern "C" int ur_uniracers_modern_controls_active(void)', start)
        body = source[start:end]

        regional = body.index("regional_input_coordinator().keyboard_key")
        help_shortcut = body.index("key == SDLK_F1")
        self.assertLess(regional, help_shortcut)
        self.assertIn("SDL_GetTicks()", body)
        self.assertIn(
            'apply_regional_input_decision(regional, "keyboard")',
            body,
        )

    def test_title_context_is_guest_state_and_text_entry_gated(self):
        source = self.source
        self.assertIn(
            "g_profile_edit_mode != ProfileEditMode::None",
            source,
        )
        self.assertIn("g_ram[0x0313] == 0x01", source)
        self.assertIn("g_ram[0x009F]", source)
        self.assertIn("regional_secret_context(", source)

    def test_semantic_controller_route_uses_mapped_snes_controls(self):
        source = self.source
        start = source.index(
            'extern "C" int ur_uniracers_modern_system_gamepad_control(')
        end = source.index(
            'extern "C" void ur_uniracers_modern_system_overlay(', start)
        body = source[start:end]

        self.assertIn("RegionalControllerAction::Left", body)
        self.assertIn("RegionalControllerAction::Right", body)
        self.assertIn("RegionalControllerAction::Accept", body)
        self.assertIn("RegionalControllerAction::ShoulderL", body)
        self.assertIn("RegionalControllerAction::ShoulderR", body)
        self.assertIn("regional_input_coordinator().controller_button", body)
        self.assertIn(
            'apply_regional_input_decision(regional, "controller")',
            body,
        )

    def test_save_required_uses_existing_host_product_store(self):
        source = self.source
        start = source.index("bool apply_regional_input_decision(")
        end = source.index("void apply_profile_save_root()", start)
        body = source[start:end]

        self.assertIn("RegionalPresentationUpdate::SaveRequired", body)
        self.assertIn("persist_product_state(g_product_state)", body)
        self.assertIn("UR_REGIONAL SWITCH", body)

    def test_loaded_state_reports_region_for_fresh_process_acceptance(self):
        self.assertIn(
            "UR_HOST_STATE LOADED regional_presentation=%s",
            self.source,
        )


if __name__ == "__main__":
    unittest.main()
