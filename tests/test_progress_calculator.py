"""Regression tests for the frozen progress inventory; no ROM or external dependencies."""
import copy
import json
import unittest
from pathlib import Path
from tools.progress_calculator import calculate, WEIGHTS

ROOT = Path(__file__).resolve().parents[1]

class ProgressCalculatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads((ROOT / "docs/PROGRESS-INVENTORY.json").read_text())
        cls.ledger = json.loads((ROOT / "docs/RELEASE-QUALITY-LEDGER.json").read_text())

    def test_current_score(self):
        result = calculate(self.inventory, self.ledger, 0)
        self.assertEqual(sum(WEIGHTS.values()), 100)
        self.assertEqual(result["engineering_maturity_percent"], 48.5)
        self.assertEqual(result["accepted_inventory_percent"], 0)
        self.assertEqual(result["windows_release_gates_passed"], 0)
        self.assertEqual(result["independent_usa_events_passed"], 0)

    def test_weight_tamper_rejected(self):
        data = copy.deepcopy(self.inventory)
        data["items"][0]["weight"] += 1
        with self.assertRaisesRegex(ValueError, "weight"):
            calculate(data, self.ledger)

    def test_duplicate_id_rejected(self):
        data = copy.deepcopy(self.inventory)
        data["items"][1]["id"] = data["items"][0]["id"]
        with self.assertRaises(ValueError):
            calculate(data, self.ledger)

    def test_unverified_acceptance_rejected(self):
        data = copy.deepcopy(self.inventory)
        data["items"][0]["status"] = "accepted"
        with self.assertRaisesRegex(ValueError, "acceptance evidence"):
            calculate(data, self.ledger)

    def test_stage_and_evidence_required(self):
        data = copy.deepcopy(self.inventory)
        data["items"][0]["evidence"] = None
        with self.assertRaisesRegex(ValueError, "repository evidence"):
            calculate(data, self.ledger)
        data = copy.deepcopy(self.inventory)
        data["items"][0]["status"] = "almost_done"
        with self.assertRaisesRegex(ValueError, "Unknown status"):
            calculate(data, self.ledger)

    def test_fake_gate_rejected(self):
        data = copy.deepcopy(self.ledger)
        data["gates"][0]["id"] = "QA-12"
        with self.assertRaisesRegex(ValueError, "gate IDs"):
            calculate(self.inventory, data)

    def test_events_are_explicit_and_bounded(self):
        self.assertIsNone(calculate(self.inventory, self.ledger)["independent_usa_events_passed"])
        with self.assertRaises(ValueError):
            calculate(self.inventory, self.ledger, 46)

if __name__ == "__main__":
    unittest.main()
