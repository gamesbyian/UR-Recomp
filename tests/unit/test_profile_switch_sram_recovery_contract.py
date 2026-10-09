"""QA-02: do not claim a profile switch if its framework SRAM is uncommitted."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ProfileSwitchSramRecoveryContract(unittest.TestCase):
    def test_profile_switch_has_exact_cas_recovery_and_sram_preflight(self):
        host = (ROOT / "native/product/uniracers_modern_host.cpp").read_text(
            encoding="utf-8"
        )
        activation = host.split("bool activate_profile_id(", 1)[1].split(
            "\n}\n\nbool create_profile_from_editor", 1
        )[0]
        self.assertIn("previous_sram", activation)
        self.assertIn("const auto previous_product = g_product_state;", activation)
        self.assertIn("if (!g_sram ||", activation)
        self.assertIn("persist_product_state(product)", activation)
        self.assertIn("persist_product_state(previous_product)", activation)
        self.assertIn("UR_PROFILE_SELECT ROLLBACK_CONFLICT_OR_IO", activation)
        self.assertIn("if (!RtlTryWriteSram())", activation)
        self.assertNotIn("(void)RtlTryWriteSram()", activation)
        self.assertLess(
            activation.index("if (!g_sram ||"),
            activation.index("persist_product_state(product)"),
        )
        self.assertLess(
            activation.index("persist_product_state(previous_product)"),
            activation.index("std::memcpy(g_sram, previous_sram"),
        )


if __name__ == "__main__":
    unittest.main()
