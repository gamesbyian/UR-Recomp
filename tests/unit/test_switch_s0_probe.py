import json
import tempfile
import unittest
from pathlib import Path

from tools.check_switch_s0_probe import check_contract

ROOT = Path(__file__).resolve().parents[2]


class SwitchS0ProbeTest(unittest.TestCase):
    def test_repository_contract_is_coherent(self):
        self.assertEqual(check_contract(ROOT), [])

    def test_contract_is_compile_only(self):
        contract = json.loads((ROOT / "analysis/switch-s0-contract.json").read_text())
        self.assertEqual(contract["gate"], "S0")
        self.assertFalse(contract["scope"]["guest_code"])
        self.assertFalse(contract["scope"]["runtime_hardware_acceptance"])
        self.assertFalse(contract["scope"]["simulation_claim"])
        self.assertFalse(contract["scope"]["product_feature_claim"])

    def test_mutable_container_tag_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in (
                "analysis/switch-s0-contract.json",
                "platform/switch/s0_probe/Makefile",
                "platform/switch/s0_probe/source/main.c",
                ".github/workflows/switch-s0-compile-probe.yml",
            ):
                src = ROOT / rel
                dst = root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(src.read_text())

            contract_path = root / "analysis/switch-s0-contract.json"
            contract = json.loads(contract_path.read_text())
            contract["toolchain"]["container"] = "devkitpro/devkita64:latest"
            contract_path.write_text(json.dumps(contract))

            errors = check_contract(root)
            self.assertTrue(any("dated devkitpro/devkita64 tag" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
