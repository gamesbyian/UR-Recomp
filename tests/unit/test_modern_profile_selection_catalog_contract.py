"""ROM-free host contract: selection must revalidate canonical racer identity.

The catalog codec's own tests cover parsing and CAS. These checks pin the
ordering of the product-facing selection preflight and its modal failure path.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "native/product/uniracers_modern_host.cpp"


def between(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


class ModernProfileSelectionCatalogContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = HOST.read_text(encoding="utf-8")
        cls.select = between(cls.host, "bool activate_profile_id(const std::string& profile_id) {",
                             "\n}\n\nbool create_profile_from_editor()")

    def test_selection_reads_canonical_catalog_before_target_state(self):
        self.assertIn("load_host_profile_catalog_file(", self.select)
        self.assertLess(self.select.index("load_host_profile_catalog_file("),
                        self.select.index("load_host_profile_state_file("))
        self.assertLess(self.select.index("if (*latest_catalog != g_profile_catalog) {"),
                        self.select.index("persist_live_profile_snapshot()"))

    def test_unreadable_catalog_blocks_selection_without_writing(self):
        unavailable = between(self.select, "if (!latest_catalog) {", "\n    }")
        self.assertIn("g_profile_catalog_refresh_failed = true;", unavailable)
        self.assertIn('UR_PROFILE_SELECT CATALOG_UNAVAILABLE', unavailable)
        self.assertIn("return false;", unavailable)
        self.assertLess(self.select.index("if (!latest_catalog) {"),
                        self.select.index("persist_live_profile_snapshot()"))

    def test_changed_catalog_requires_explicit_retry_by_immutable_id(self):
        changed = between(self.select, "if (*latest_catalog != g_profile_catalog) {", "\n    }")
        self.assertIn("g_profile_catalog = *latest_catalog;", changed)
        self.assertIn("g_profile_catalog[i].profile_id == profile_id", changed)
        self.assertIn('UR_PROFILE_SELECT CATALOG_CHANGED_RETRY', changed)
        self.assertIn("return false;", changed)
        self.assertNotIn("activate_profile_id(", changed)

    def test_modal_enter_consumption_and_authorization_still_apply(self):
        handler = between(self.host, "bool handle_profile_menu_key(int key) {",
                          "\n}\n\nvoid project_profile_identity_to_stock_rider")
        self.assertIn("g_profile_select_failed = !selected;", handler)
        self.assertIn("return true;", handler)
        self.assertIn("profile_catalog_authorizes_state(", self.select)
        self.assertIn("persist_product_state(product)", self.select)


if __name__ == "__main__":
    unittest.main()
