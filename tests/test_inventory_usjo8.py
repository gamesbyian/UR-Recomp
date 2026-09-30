#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "inventory_usjo8.py"
SPEC = importlib.util.spec_from_file_location("inventory_usjo8", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Usjo8InventoryTests(unittest.TestCase):
    def test_generated_inventory_is_fresh(self):
        source = ROOT / "references" / "imported" / "tas-bots" / "usjo8.lua"
        generated = ROOT / "analysis" / "generated" / "usjo8-static-inventory.json"
        expected = json.loads(generated.read_text(encoding="utf-8"))
        actual = MODULE.build_inventory(source)
        actual["source"] = "references/imported/tas-bots/usjo8.lua"
        self.assertEqual(actual, expected)

    def test_recovered_read_surface_is_explicit(self):
        source = ROOT / "references" / "imported" / "tas-bots" / "usjo8.lua"
        data = MODULE.build_inventory(source)
        self.assertEqual(
            set(data["memory_reads_by_address"]),
            {
                "0x7E04B7",
                "0x7E04BB",
                "0x7E0545",
                "0x7E0F61",
                "0x7E042F",
                "0x7E042B",
                "0x7E11F9",
                "0x7E11FD",
                "0x7E0DFD",
                "0x7E0F57",
                "0x7E11CD",
            },
        )
        self.assertEqual(data["boost_scoring_block"]["start_line"], 946)
        self.assertEqual(data["boost_scoring_block"]["end_line"], 995)
        self.assertEqual(data["controller_output_block"]["start_line"], 1392)
        self.assertEqual(data["controller_output_block"]["end_line"], 1446)


if __name__ == "__main__":
    unittest.main()
