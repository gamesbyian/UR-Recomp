"""ROM-free source contract: reset must revalidate racer authorization before mutation.

Native Windows concurrency and crash-recovery behavior remain independent QA.
"""
from pathlib import Path
import unittest

HOST = Path(__file__).resolve().parents[2] / "native/product/uniracers_modern_host.cpp"


def between(source, start, end):
    return source.split(start, 1)[1].split(end, 1)[0]


class ProfileResetCatalogPreflightContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = HOST.read_text(encoding="utf-8")
        cls.reset = between(source, "bool execute_active_profile_progress_reset() {",
                            "\n}\n\nvoid open_profile_reset_confirmation")
        cls.handler = between(source, "bool handle_profile_menu_key(int key) {",
                              "\n}\n\nvoid project_profile_identity_to_stock_rider")

    def test_canonical_roster_is_read_before_any_snapshot_write(self):
        self.assertIn("load_host_profile_catalog_file(", self.reset)
        self.assertLess(self.reset.index("load_host_profile_catalog_file("),
                        self.reset.index("save_host_profile_state_file_if_current("))
        self.assertLess(self.reset.index("load_host_profile_catalog_file("),
                        self.reset.index("std::memcpy(g_sram, reset_sram.data()"))

    def test_unreadable_catalog_fails_closed(self):
        block = between(self.reset, "if (!latest_catalog) {", "\n    }")
        self.assertIn("g_profile_catalog_refresh_failed = true;", block)
        self.assertIn('UR_PROFILE_RESET CATALOG_UNAVAILABLE', block)
        self.assertIn("return false;", block)

    def test_changed_catalog_reselects_immutable_active_racer_and_requires_retry(self):
        block = between(self.reset, "if (*latest_catalog != g_profile_catalog) {", "\n    }")
        self.assertIn("g_profile_catalog = *latest_catalog;", block)
        self.assertIn("entry.profile_id == *g_product_state.active_profile_id", block)
        self.assertIn("g_profile_menu_index", block)
        self.assertIn('UR_PROFILE_RESET CATALOG_CHANGED_RETRY', block)
        self.assertIn("return false;", block)

    def test_active_identity_and_catalog_authorization_guard_reset(self):
        self.assertIn("g_profile_state->profile_id != *g_product_state.active_profile_id", self.reset)
        self.assertIn("profile_catalog_authorizes_state(", self.reset)
        self.assertLess(self.reset.index("profile_catalog_authorizes_state("),
                        self.reset.index("auto reset_sram ="))
        self.assertIn("execute_active_profile_progress_reset()", self.handler)
        self.assertIn("ProfileResetNotice::Failed", self.handler)


if __name__ == "__main__":
    unittest.main()
