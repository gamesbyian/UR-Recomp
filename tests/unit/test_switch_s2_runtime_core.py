import unittest

from tools.build_switch_s2_runtime_probe import load_contract


class SwitchS2RuntimeCoreContractTest(unittest.TestCase):
    def test_contract_excludes_desktop_sources(self):
        contract = load_contract()
        self.assertEqual(contract["gate"], "S2-runtime-core-portability")
        self.assertGreaterEqual(len(contract["runtime_sources"]), 30)
        self.assertFalse(
            any("/desktop/" in source for source in contract["runtime_sources"])
        )
        self.assertIn("variables.h", contract["boundary_headers"])
        self.assertIn("config.h", contract["boundary_headers"])

    def test_contract_keeps_switch_compile_separate_from_s2_acceptance(self):
        contract = load_contract()
        self.assertTrue(any("does not close Gate S2" in item for item in contract["non_claims"]))
        self.assertTrue(any("__SWITCH__" == item for item in contract["compile_definitions"]))


if __name__ == "__main__":
    unittest.main()
