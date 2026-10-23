"""Guard Modern profile rename against stale catalog-index retargeting.

This source-bound test is deliberately ROM-free. Native Windows/profile
concurrency and persistence acceptance remain separate integration evidence.
"""
from pathlib import Path
import unittest

HOST = Path(__file__).resolve().parents[2] / "native/product/uniracers_modern_host.cpp"


def section(source, begin, end):
    return source.split(begin, 1)[1].split(end, 1)[0]


class ProfileRenameIdentityContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HOST.read_text(encoding="utf-8")

    def test_rename_rebinds_by_immutable_id_before_mutating(self):
        rename = section(self.source, "bool rename_profile_from_editor() {",
                         "\n}\n\nvoid open_profile_menu()")
        self.assertIn("g_profile_edit_target_id.empty()", rename)
        self.assertIn("entry.profile_id == g_profile_edit_target_id", rename)
        self.assertIn("if (target == g_profile_catalog.end())", rename)
        self.assertLess(rename.index("if (target == g_profile_catalog.end())"),
                        rename.index("auto& entry = *target;"))
        self.assertNotIn("auto& entry = g_profile_catalog[g_profile_menu_index]", rename)
        self.assertIn("g_profile_edit_target_id.clear();", rename)

    def test_target_captured_on_rename_and_cleared_on_new_editor(self):
        begin = section(self.source, "void begin_profile_rename() {",
                        "\n}\n\nbool selected_profile_is_active()")
        self.assertIn("g_profile_edit_target_id =", begin)
        self.assertIn("g_profile_catalog[g_profile_menu_index].profile_id", begin)
        create = section(self.source, "void begin_profile_create() {",
                         "\n}\n\nvoid begin_profile_rename()")
        self.assertIn("g_profile_edit_target_id.clear();", create)
        opened = section(self.source, "void open_profile_menu() {",
                         "\n}\n\nvoid begin_profile_create()")
        self.assertIn("g_profile_edit_target_id.clear();", opened)

    def test_catalog_index_clamped_before_chooser_draw_and_dispatch(self):
        self.assertIn("void reconcile_profile_menu_index()", self.source)
        reconcile = section(self.source, "void reconcile_profile_menu_index() {",
                            "\n}\n\n")
        self.assertIn("g_profile_catalog.empty()", reconcile)
        self.assertIn("g_profile_menu_index >= g_profile_catalog.size()", reconcile)
        handler = section(self.source, "bool handle_profile_menu_key(int key) {",
                          "\n}\n\nvoid project_profile_identity_to_stock_rider")
        self.assertIn("ensure_profile_catalog();\n    reconcile_profile_menu_index();", handler)
        overlay = section(self.source, "if (g_profile_menu_visible && modern_mode()) {",
                          "\n    if (g_modern_root_stock_target >= 0")
        self.assertIn("ensure_profile_catalog();\n        reconcile_profile_menu_index();", overlay)

    def test_escape_drops_stale_rename_target(self):
        handler = section(self.source, "bool handle_profile_menu_key(int key) {",
                          "\n}\n\nvoid project_profile_identity_to_stock_rider")
        editor = section(handler, "if (g_profile_edit_mode != ProfileEditMode::None) {",
                         "\n    if (key == SDLK_ESCAPE || key == SDLK_F2)")
        self.assertIn("g_profile_edit_target_id.clear();", editor)


if __name__ == "__main__":
    unittest.main()
