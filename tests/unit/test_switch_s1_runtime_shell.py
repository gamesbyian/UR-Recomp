import json
import unittest
from pathlib import Path

from tools.check_switch_s1_runtime_shell import check

ROOT = Path(__file__).resolve().parents[2]

class SwitchS1RuntimeShellTest(unittest.TestCase):
    def test_repository_contract_is_coherent(self):
        self.assertEqual(check(ROOT), [])

    def test_ci_does_not_claim_hardware_acceptance(self):
        contract = json.loads(
            (ROOT / "analysis/switch-s1-runtime-shell-contract.json").read_text()
        )
        self.assertEqual(contract["gate"], "S1-runtime-shell")
        self.assertGreaterEqual(len(contract["non_claims"]), 5)
        for capability in contract["capabilities"].values():
            self.assertIn("hardware", capability)
            self.assertIn("ci", capability)

if __name__ == "__main__":
    unittest.main()
