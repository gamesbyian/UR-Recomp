import unittest

from tools.analyze_switch_s2_link_surface import classify, load_contract


class SwitchS2LinkSurfaceTest(unittest.TestCase):
    def test_classifier_separates_known_libc_from_host_symbols(self):
        contract = load_contract()
        result = classify(["malloc", "__aeabi_memcpy", "RtlApuLock", "MkDir"], contract)
        self.assertIn("malloc", result["libc_or_toolchain"])
        self.assertIn("__aeabi_memcpy", result["libc_or_toolchain"])
        self.assertIn("RtlApuLock", result["host_or_runtime"])
        self.assertIn("MkDir", result["host_or_runtime"])

    def test_contract_does_not_claim_full_link(self):
        contract = load_contract()
        self.assertEqual(contract["gate"], "S2-link-surface")
        self.assertTrue(any("not a runnable NRO" in item for item in contract["non_claims"]))


if __name__ == "__main__":
    unittest.main()
