#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools" / "compare_fixture_cdl.py"

spec = importlib.util.spec_from_file_location("compare_fixture_cdl", PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class CompareFixtureCdlTests(unittest.TestCase):
    def test_lorom_cpu_address(self):
        self.assertEqual(mod.lorom_cpu_address(0x000000), "00:8000")
        self.assertEqual(mod.lorom_cpu_address(0x007FFF), "00:FFFF")
        self.assertEqual(mod.lorom_cpu_address(0x008000), "01:8000")
        self.assertEqual(mod.lorom_cpu_address(0x012345), "02:A345")

    def test_ranges_coalesces_adjacent_offsets(self):
        self.assertEqual(mod.ranges([1, 2, 3, 7, 9, 10]), [(1, 3), (7, 7), (9, 10)])

    def test_compare_entries_tracks_directional_code_and_data(self):
        baseline = [
            {"code": True},
            {"data": True},
            {"code": True, "data": True},
            {},
            {},
        ]
        variant = [
            {"code": True},
            {},
            {"code": True, "data": True},
            {"code": True},
            {"data": True},
        ]
        result = mod.compare_entries(baseline, variant)
        self.assertEqual(result["code"]["variant_only"], 1)
        self.assertEqual(result["code"]["baseline_only"], 0)
        self.assertEqual(
            result["code"]["variant_only_ranges"],
            [{"start": 3, "end": 3, "length": 1, "cpu_start": "00:8003", "cpu_end": "00:8003"}],
        )
        self.assertEqual(result["data"]["variant_only"], 1)
        self.assertEqual(result["data"]["baseline_only"], 1)

    def test_compare_entries_rejects_different_map_sizes(self):
        with self.assertRaisesRegex(ValueError, "CDL map size mismatch"):
            mod.compare_entries([{}], [{}, {}])


if __name__ == "__main__":
    unittest.main()
