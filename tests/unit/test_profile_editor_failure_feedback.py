"""Source-bound contract for visible, modal Modern profile editor failures.

The native host requires SDL/guest dependencies; these assertions guard the
input/overlay wiring until the regular native/Windows CI qualifies the change.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


def between(text: str, begin: str, end: str) -> str:
    return text.split(begin, 1)[1].split(end, 1)[0]


class ProfileEditorFailureFeedbackContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HOST.read_text(encoding="utf-8")

    def test_failed_create_and_rename_remain_modal_and_visible(self):
        handler = between(self.source, "bool handle_profile_menu_key(int key) {",
                          "\n}\n\nvoid project_profile_identity_to_stock_rider")
        editor = between(handler, "if (g_profile_edit_mode != ProfileEditMode::None) {",
                         "\n    if (key == SDLK_ESCAPE || key == SDLK_F2)")
        self.assertIn("? create_profile_from_editor()", editor)
        self.assertIn(": rename_profile_from_editor();", editor)
        self.assertIn("g_profile_edit_save_failed =\n", editor)
        self.assertIn("g_profile_edit_mode != ProfileEditMode::None;", editor)
        self.assertIn('product_diagnostic("UR_PROFILE_UI SAVE_REJECTED")', editor)
        self.assertIn("// The profile editor is modal.", editor)
        self.assertIn("return true;", editor.split("// The profile editor is modal.", 1)[1])
        self.assertNotIn("return saved;", editor)

    def test_committed_create_with_failed_activation_reports_chooser_failure(self):
        handler = between(self.source, "bool handle_profile_menu_key(int key) {",
                          "\n}\n\nvoid project_profile_identity_to_stock_rider")
        editor = between(handler, "if (g_profile_edit_mode != ProfileEditMode::None) {",
                         "\n    if (key == SDLK_ESCAPE || key == SDLK_F2)")
        self.assertIn("if (!g_profile_edit_save_failed) {", editor)
        self.assertIn("g_profile_select_failed = true;", editor)
        self.assertIn("g_profile_cool_name_notice = false;", editor)
        self.assertIn('"SELECT FAILED - ESC TO CLOSE"', self.source)

    def test_notice_resets_on_retry_edit_navigation_and_reopen(self):
        for name, stop in [
            ("void open_profile_menu() {", "\n}\n\nvoid begin_profile_create"),
            ("void begin_profile_create() {", "\n}\n\nvoid begin_profile_rename"),
            ("void begin_profile_rename() {", "\n}\n\nbool selected_profile_is_active"),
            ("bool append_profile_editor_key(int key) {", "\n}\n\nbool handle_profile_menu_key"),
        ]:
            self.assertIn("g_profile_edit_save_failed = false;",
                          between(self.source, name, stop))
        handler = between(self.source, "bool handle_profile_menu_key(int key) {",
                          "\n}\n\nvoid project_profile_identity_to_stock_rider")
        self.assertGreaterEqual(handler.count("g_profile_edit_save_failed = false;"), 3)

    def test_editor_notice_is_rendered_without_overwriting_save_controls(self):
        overlay = between(self.source, '"ENTER SAVE   ESC CANCEL", 0xFFFFFFFFu, scale);',
                          '} else if (g_profile_catalog.empty()) {')
        self.assertIn("if (g_profile_edit_save_failed) {", overlay)
        notice = "SAVE FAILED - NAME OR DISK"
        self.assertIn(f'"{notice}"', overlay)
        self.assertIn("y + 137 * scale", overlay)
        # The 256-wide canvas uses a 240-pixel modal with 8px inset on each side.
        self.assertLessEqual(len(notice) * 8, 240 - 16)


if __name__ == "__main__":
    unittest.main()
