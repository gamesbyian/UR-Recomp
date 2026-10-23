"""The Modern profile chooser owns Enter even when activation is refused."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


class ProfileSelectionModalContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HOST.read_text(encoding="utf-8")

    def test_failed_profile_activation_does_not_release_enter_to_stock(self):
        body = self.source.split("bool handle_profile_menu_key(int key) {", 1)[1].split(
            "\n}\n\nvoid project_profile_identity_to_stock_rider", 1
        )[0]
        # The old `return activate_profile_id(...)` propagated a false result
        # to the keyboard dispatcher, releasing the same Enter to the guest.
        self.assertNotIn("return activate_profile_id(", body)
        confirm = body.split("if (key == SDLK_RETURN || key == SDLK_KP_ENTER) {", 2)[-1]
        self.assertIn("const bool selected = activate_profile_id(", confirm)
        self.assertIn("g_profile_select_failed = !selected;", confirm)
        self.assertIn("return true;", confirm)
        self.assertIn("return handle_profile_menu_key(key) ? 1 : 0;", self.source)

    def test_rejected_selection_is_visible_and_recoverable(self):
        body = self.source.split("bool handle_profile_menu_key(int key) {", 1)[1].split(
            "\n}\n\nvoid project_profile_identity_to_stock_rider", 1
        )[0]
        opened = self.source.split("void open_profile_menu() {", 1)[1].split(
            "\n}\n\nvoid begin_profile_create", 1
        )[0]
        self.assertIn("g_profile_select_failed = false;", opened)
        self.assertGreaterEqual(body.count("g_profile_select_failed = false;"), 2)
        self.assertIn('"UR_PROFILE_UI SELECT_REJECTED"', body)
        self.assertIn('"SELECT FAILED - ESC TO CLOSE"', self.source)
        self.assertIn("g_profile_select_failed", self.source)


if __name__ == "__main__":
    unittest.main()
