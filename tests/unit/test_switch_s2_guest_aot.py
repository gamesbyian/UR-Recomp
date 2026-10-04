import json
import tempfile
import unittest
from pathlib import Path

from tools.build_switch_s2_guest_probe import load_contract, validate_bundle

ROOT = Path(__file__).resolve().parents[2]


class SwitchS2GuestAotContractTest(unittest.TestCase):
    def test_contract_is_bounded_and_does_not_claim_s2_closed(self):
        contract = load_contract()
        self.assertEqual(contract["gate"], "S2-guest-aot-portability")
        self.assertIn("src/main.c", contract["excluded_sources"])
        self.assertTrue(any("does not close Gate S2" in item for item in contract["non_claims"]))

    def test_minimal_bundle_requires_generated_c(self):
        contract = load_contract()
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            for rel in (
                "project/src/game_rtl.c",
                "project/src/host_contract.c",
                "project/src/gen_stubs.c",
                "project/recomp/funcs.h",
                "framework/runner/src/common_cpu_infra.h",
                "framework/runner/src/common_rtl.h",
                "framework/runner/src/snes/snes.h",
            ):
                path = bundle / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("/* fixture */\n")
            sources, errors = validate_bundle(bundle, contract)
            self.assertEqual(len(sources), 3)
            self.assertTrue(any("no src/gen" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
