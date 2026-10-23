"""ROM-free contract for fresh, fail-closed Modern profile chooser roster reads.

The catalog codec's own tests cover serialization and file errors; these
assertions protect the host integration and modal failure behavior.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "native/product/uniracers_modern_host.cpp"
CATALOG = ROOT / "native/product/host_profile_catalog.cpp"


def between(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


class ModernProfileCatalogRefreshContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = HOST.read_text(encoding="utf-8")
        cls.catalog = CATALOG.read_text(encoding="utf-8")

    def test_open_refreshes_disk_even_with_cached_roster(self):
        opened = between(self.host, "void open_profile_menu() {", "\n}\n\nvoid begin_profile_create()")
        self.assertIn("load_host_profile_catalog_file(", opened)
        self.assertIn("g_profile_catalog = *current_catalog;", opened)
        self.assertIn("g_profile_catalog_refresh_failed = !current_catalog.has_value();", opened)
        self.assertLess(opened.index("g_profile_catalog = *current_catalog;"),
                        opened.index("g_profile_menu_index = 0;"))
        self.assertIn("*g_product_state.active_profile_id", opened)

    def test_unreadable_catalog_is_fail_closed_for_every_modal_action(self):
        handler = between(self.host, "bool handle_profile_menu_key(int key) {",
                          "\n}\n\nvoid project_profile_identity_to_stock_rider")
        self.assertIn("if (g_profile_catalog_refresh_failed) {", handler)
        guard = between(handler, "if (g_profile_catalog_refresh_failed) {", "\n    }")
        self.assertIn("key == SDLK_ESCAPE || key == SDLK_F2", guard)
        self.assertIn("g_profile_menu_visible = false;", guard)
        self.assertIn("return true;", guard)
        self.assertLess(handler.index("if (g_profile_catalog_refresh_failed) {"),
                        handler.index("if (ur::product::modern_profile_reset_confirming"))
        self.assertLess(handler.index("if (g_profile_catalog_refresh_failed) {"),
                        handler.index("if (key == SDLK_n)"))

    def test_failure_is_visible_and_reopen_can_retry(self):
        overlay = between(self.host, "if (g_profile_menu_visible && modern_mode()) {",
                          "\n    if (g_modern_root_stock_target >= 0")
        self.assertIn("if (g_profile_catalog_refresh_failed) {", overlay)
        self.assertIn('"CATALOG UNAVAILABLE"', overlay)
        self.assertIn('"ESC / F2 CLOSE - RETRY"', overlay)
        self.assertLess(overlay.index("if (g_profile_catalog_refresh_failed) {"),
                        overlay.index("if (ur::product::modern_profile_reset_confirming"))

    def test_missing_is_empty_but_corrupt_is_unavailable(self):
        load = between(self.catalog, "load_host_profile_catalog_file(\n",
                       "\n}\n\nstd::string make_profile_id(")
        self.assertIn("if (!exists) return std::vector<HostProfileCatalogEntry>{};", load)
        self.assertIn("if (!data) return std::nullopt;", load)
        self.assertIn("return decode_host_profile_catalog(*data);", load)


    def test_create_revalidates_catalog_before_profile_directory_write(self):
        create = between(self.host, "bool create_profile_from_editor() {",
                         "\n}\n\nbool rename_profile_from_editor()")
        self.assertIn("const auto latest_catalog = ur::product::load_host_profile_catalog_file(", create)
        self.assertIn("if (!latest_catalog) {", create)
        self.assertIn("g_profile_catalog_refresh_failed = true;", create)
        self.assertIn("if (*latest_catalog != g_profile_catalog) {", create)
        self.assertIn("g_profile_catalog = *latest_catalog;", create)
        self.assertLess(create.index("if (*latest_catalog != g_profile_catalog) {"),
                        create.index("make_profile_id("))
        self.assertLess(create.index("if (*latest_catalog != g_profile_catalog) {"),
                        create.index("std::filesystem::create_directories("))

    def test_stale_create_returns_without_publishing_profile_state(self):
        create = between(self.host, "bool create_profile_from_editor() {",
                         "\n}\n\nbool rename_profile_from_editor()")
        stale = between(create, "if (*latest_catalog != g_profile_catalog) {", "\n    }")
        self.assertIn("g_profile_catalog = *latest_catalog;", stale)
        self.assertIn("return false;", stale)
        unavailable = between(create, "if (!latest_catalog) {", "\n    }")
        self.assertIn("g_profile_catalog_refresh_failed = true;", unavailable)
        self.assertIn("return false;", unavailable)
        self.assertLess(create.index("if (!latest_catalog) {"),
                        create.index("save_host_profile_state_file_if_current("))

if __name__ == "__main__":
    unittest.main()
