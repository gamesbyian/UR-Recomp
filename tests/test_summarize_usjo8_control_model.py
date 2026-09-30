#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "summarize_usjo8_control_model.py"
SPEC = importlib.util.spec_from_file_location("summarize_usjo8_control_model", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Usjo8ControlModelTests(unittest.TestCase):
    def test_generated_control_model_is_fresh(self):
        inventory = json.loads((ROOT / "analysis/generated/usjo8-static-inventory.json").read_text(encoding="utf-8"))
        expected = json.loads((ROOT / "analysis/generated/usjo8-control-model.json").read_text(encoding="utf-8"))
        self.assertEqual(MODULE.build_model(inventory), expected)

    def test_recovered_domains(self):
        inventory = json.loads((ROOT / "analysis/generated/usjo8-static-inventory.json").read_text(encoding="utf-8"))
        model = MODULE.build_model(inventory)
        self.assertEqual(model["states"]["tabletopstatus"]["values"], ["0", "1", "2", "6"])
        self.assertEqual(model["states"]["mode"]["values"], ["1", "2", "3", "4", "5"])


if __name__ == "__main__":
    unittest.main()
