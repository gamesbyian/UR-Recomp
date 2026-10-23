"""Source-bound regression for failed Modern profile progress reset feedback.

The native host needs SDL/guest dependencies; these assertions validate
wiring and presentation pending native Windows CI and independent review.
"""
from pathlib import Path
import unittest

HOST = Path(__file__).resolve().parents[2] / "native/product/uniracers_modern_host.cpp"


def section(source, begin, end):
    return source.split(begin, 1)[1].split(end, 1)[0]


class ProfileResetFailureFeedbackContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HOST.read_text(encoding="utf-8")

    def test_reset_failure_and_rejected_context_have_distinct_notices(self):
        opened = section(self.source, "void open_profile_reset_confirmation() {",
                         "\n}\n\nbool append_profile_editor_key")
        self.assertIn("g_profile_reset_notice = ProfileResetNotice::None;", opened)
        self.assertIn("g_profile_reset_notice = ProfileResetNotice::Unavailable;", opened)
        handler = section(self.source, "bool handle_profile_menu_key(int key) {",
                          "\n}\n\nvoid project_profile_identity_to_stock_rider")
        self.assertIn("execute_active_profile_progress_reset()", handler)
        self.assertIn("ProfileResetNotice::Failed", handler)
        self.assertIn("ProfileResetNotice::Unavailable", handler)
        self.assertIn("g_profile_reset = decision.state;", handler)
        self.assertIn("return true;", handler.split("g_profile_reset = decision.state;", 1)[1])

    def test_notice_clears_on_cancel_reopen_edit_and_selection(self):
        for start, end in [
            ("void open_profile_menu() {", "\n}\n\nvoid begin_profile_create"),
            ("void begin_profile_create() {", "\n}\n\nvoid begin_profile_rename"),
            ("void begin_profile_rename() {", "\n}\n\nbool selected_profile_is_active"),
        ]:
            self.assertIn("g_profile_reset_notice = ProfileResetNotice::None;",
                          section(self.source, start, end))
        handler = section(self.source, "bool handle_profile_menu_key(int key) {",
                          "\n}\n\nvoid project_profile_identity_to_stock_rider")
        self.assertIn("g_profile_reset_notice = ProfileResetNotice::None;", handler)
        self.assertGreaterEqual(handler.count(
            "g_profile_reset_notice = ProfileResetNotice::None;"), 4)

    def test_notice_is_visible_for_empty_and_populated_chooser(self):
        overlay = section(self.source,
                          "if (g_profile_menu_visible && modern_mode()) {",
                          "\n    if (g_modern_root_stock_target >= 0")
        empty = section(overlay, "} else if (g_profile_catalog.empty()) {",
                        "} else {")
        populated = section(overlay, "} else {\n            const auto& entry",
                            "\n        if (g_profile_cool_name_notice)")
        self.assertIn("profile_reset_notice_text()", empty)
        self.assertIn("profile_reset_notice_text()", populated)
        self.assertIn("y + 112 * scale", empty)
        self.assertIn("y + 137 * scale", populated)
        for notice in ("RESET UNAVAILABLE", "RESET FAILED - DISK/STATE"):
            self.assertIn(notice, self.source)
            self.assertLessEqual(len(notice) * 8, 240 - 16)

    def test_notice_never_overwrites_confirm_modal(self):
        overlay = section(self.source,
                          "if (g_profile_menu_visible && modern_mode()) {",
                          "\n    if (g_modern_root_stock_target >= 0")
        confirm = section(overlay,
                          "if (ur::product::modern_profile_reset_confirming(",
                          "} else if (g_profile_edit_mode != ProfileEditMode::None)")
        self.assertNotIn("profile_reset_notice_text()", confirm)


if __name__ == "__main__":
    unittest.main()
