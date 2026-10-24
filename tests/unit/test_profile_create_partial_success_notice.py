"""ROM-free contract: a committed new racer must not be reported as an unsaved racer.

A successful catalog commit followed by failed activation leaves the new racer
in the chooser. Native Windows fault and cold-reopen QA remain independent.
"""
from pathlib import Path
import unittest

HOST = Path(__file__).resolve().parents[2] / "native/product/uniracers_modern_host.cpp"


class ProfileCreatePartialSuccessNotice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HOST.read_text(encoding="utf-8")
        cls.create = cls.source.split("bool create_profile_from_editor() {", 1)[1].split("\n}\n\nbool rename_profile_from_editor", 1)[0]
        cls.keys = cls.source.split("bool handle_profile_menu_key(int key) {", 1)[1].split("\n}\n\nvoid project_profile_identity_to_stock_rider", 1)[0]
        cls.draw = cls.source.split("if (g_profile_menu_visible && modern_mode()) {", 1)[1].split("\n    if (g_modern_root_stock_target", 1)[0]

    def test_notice_only_follows_committed_create_and_failed_activation(self):
        self.assertLess(self.create.index("persist_profile_catalog(prior_catalog)"),
                        self.create.index("const bool activated = activate_profile_id(id);"))
        self.assertIn("g_profile_create_activation_failed = !activated;", self.create)
        self.assertLess(self.create.index("const bool activated = activate_profile_id(id);"),
                        self.create.index("g_profile_create_activation_failed = !activated;"))

    def test_chooser_explains_saved_racer_and_retry(self):
        self.assertIn("g_profile_create_activation_failed", self.draw)
        self.assertIn("RACER SAVED - ENTER TO RETRY", self.draw)
        self.assertLess(self.draw.index("g_profile_create_activation_failed"),
                        self.draw.index("SELECT FAILED - ESC TO CLOSE"))

    def test_notice_clears_on_reopen_and_new_editor(self):
        for name in ("void open_profile_menu() {", "void begin_profile_create() {", "void begin_profile_rename() {"):
            block = self.source.split(name, 1)[1].split("\n}", 1)[0]
            self.assertIn("g_profile_create_activation_failed = false;", block)

    def test_notice_clears_on_navigation_and_retry(self):
        for key in ("SDLK_UP", "SDLK_DOWN"):
            block = self.keys.split("if (key == " + key, 1)[1]
            self.assertIn("g_profile_create_activation_failed = false;", block.split("return true;", 1)[0])
        selection = self.keys.rsplit("if (key == SDLK_RETURN || key == SDLK_KP_ENTER)", 1)[1]
        self.assertIn("g_profile_create_activation_failed = false;", selection.split("return true;", 1)[0])


if __name__ == "__main__":
    unittest.main()
