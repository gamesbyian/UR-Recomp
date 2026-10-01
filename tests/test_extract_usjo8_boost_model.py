#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "extract_usjo8_boost_model.py"
SPEC = importlib.util.spec_from_file_location("extract_usjo8_boost_model", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Usjo8BoostModelTests(unittest.TestCase):
    def test_generated_model_is_fresh(self):
        source = (ROOT / "reference/imported/tas-bots/usjo8.lua").read_text(encoding="utf-8")
        expected = json.loads((ROOT / "analysis/generated/usjo8-boost-model.json").read_text(encoding="utf-8"))
        self.assertEqual(MODULE.build_model(source), expected)

    def test_key_reward_rules(self):
        source = (ROOT / "reference/imported/tas-bots/usjo8.lua").read_text(encoding="utf-8")
        model = MODULE.build_model(source)
        self.assertEqual([r["reward"] for r in model["reward_rules"]["flips"]], [176, 200, 224, 248])
        self.assertEqual([r["reward"] for r in model["reward_rules"]["rolls"]], [128, 152, 176, 200])
        self.assertEqual(model["score_rule"], "finalscore = thisboostmeter + lastspeed")


if __name__ == "__main__":
    unittest.main()
