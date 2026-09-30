#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "summarize_usjo8_validation.py"
SPEC = importlib.util.spec_from_file_location("summarize_usjo8_validation", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Usjo8ValidationMatrixTests(unittest.TestCase):
    def test_generated_matrix_is_fresh(self):
        inventory = json.loads((ROOT / "analysis/generated/usjo8-static-inventory.json").read_text(encoding="utf-8"))
        symbols = (ROOT / "docs/SYMBOLS.md").read_text(encoding="utf-8")
        expected = json.loads((ROOT / "analysis/generated/usjo8-validation-matrix.json").read_text(encoding="utf-8"))
        actual = MODULE.build_matrix(inventory, symbols)
        self.assertEqual(actual, expected)
        expected_md = (ROOT / "analysis/generated/usjo8-validation-matrix.md").read_text(encoding="utf-8")
        self.assertEqual(MODULE.render_markdown(actual), expected_md)

    def test_current_status_counts(self):
        inventory = json.loads((ROOT / "analysis/generated/usjo8-static-inventory.json").read_text(encoding="utf-8"))
        symbols = (ROOT / "docs/SYMBOLS.md").read_text(encoding="utf-8")
        matrix = MODULE.build_matrix(inventory, symbols)
        self.assertEqual(matrix["summary"], {
            "corroborated-unreproduced": 5,
            "runtime-confirmed": 3,
            "source-lead": 2,
            "strong-partial": 1,
        })


if __name__ == "__main__":
    unittest.main()
