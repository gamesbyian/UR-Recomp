"""ROM-free source contract: switching racers must not discard unsaved active SRAM.

Native Windows profile-fault/cold-reopen acceptance remains independently owned.
"""
from pathlib import Path
import unittest

HOST = Path(__file__).resolve().parents[2] / "native/product/uniracers_modern_host.cpp"


class ProfileSwitchSourceGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = HOST.read_text(encoding="utf-8")
        cls.activation = source.split("bool activate_profile_id(const std::string& profile_id) {", 1)[1].split("\n}\n\nbool create_profile_from_editor", 1)[0]

    def test_named_active_racer_must_have_writable_snapshot_before_switch(self):
        guard = self.activation.split("UR_PROFILE_SELECT REJECTED_SOURCE_SNAPSHOT", 1)[0]
        self.assertIn("g_product_state.active_profile_id", guard)
        self.assertIn("!g_profile_state", guard)
        self.assertIn("!g_profile_state_writable", guard)
        self.assertIn("g_profile_state_path.empty()", guard)
        self.assertIn("g_profile_state->profile_id != *g_product_state.active_profile_id", guard)

    def test_source_guard_runs_before_any_switch_mutation(self):
        self.assertLess(self.activation.index("UR_PROFILE_SELECT REJECTED_SOURCE_SNAPSHOT"),
                        self.activation.index("persist_live_profile_snapshot()"))
        self.assertLess(self.activation.index("UR_PROFILE_SELECT REJECTED_SOURCE_SNAPSHOT"),
                        self.activation.index("g_product_state = product;"))

    def test_guard_is_conditional_on_existing_active_identity(self):
        guard = self.activation.split("UR_PROFILE_SELECT REJECTED_SOURCE_SNAPSHOT", 1)[0]
        self.assertIn("if (g_product_state.active_profile_id &&", guard)
        self.assertIn("return false;", self.activation.split("UR_PROFILE_SELECT REJECTED_SOURCE_SNAPSHOT", 1)[1].split("\n    }", 1)[0])

    def test_existing_catalog_and_selector_guards_remain(self):
        self.assertIn("load_host_profile_catalog_file(", self.activation)
        self.assertIn("profile_catalog_authorizes_state(", self.activation)
        self.assertIn("persist_product_state(product)", self.activation)
        self.assertIn("restore_previous()", self.activation)


if __name__ == "__main__":
    unittest.main()
