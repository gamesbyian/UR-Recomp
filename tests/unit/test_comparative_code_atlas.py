#!/usr/bin/env python3
"""Unit coverage for the comparative code-atlas matcher."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_comparative_code_atlas.py"
SPEC = importlib.util.spec_from_file_location("comparative_code_atlas", TOOL)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class ComparativeCodeAtlasTests(unittest.TestCase):
    def test_exact_same_offset_relocated_and_unmatched(self) -> None:
        with tempfile.TemporaryDirectory() as td_raw:
            td = Path(td_raw)
            size = 0x10000
            roms = {name: bytearray([0xEA] * size) for name in mod.ROM_NAMES}

            a_off = 0x0100
            b_off = 0x8200
            moved = 0x9000
            a = bytes(range(32))
            b = bytes(range(32, 64))

            roms["usa"][a_off:a_off + 32] = a
            roms["usa"][b_off:b_off + 32] = b
            for name in ("europe", "beta", "prototype"):
                roms[name][a_off:a_off + 32] = a
            roms["beta"][b_off:b_off + 32] = b
            roms["europe"][b_off:b_off + 32] = bytes([0xCC] * 32)
            roms["europe"][moved:moved + 32] = b
            roms["prototype"][b_off:b_off + 32] = bytes([0xAB] * 32)

            paths = {}
            for name, blob in roms.items():
                path = td / f"{name}.sfc"
                path.write_bytes(blob)
                paths[name] = path

            symbols = td / "symbols.json"
            symbols.write_text(json.dumps({
                "entries": [
                    {"kind": "function", "address": "80:8100", "name": "A", "confidence": 5},
                    {"kind": "function", "address": "81:8200", "name": "B", "confidence": 3},
                    {"kind": "ram", "address": "7E:0000", "name": "RAM"},
                ]
            }))
            gaps = td / "gaps.json"
            gaps.write_text(json.dumps({"gaps": [
                {"id": "g1", "kind": "unresolved_indirect_dispatch", "site": "80:9000"}
            ]}))

            atlas = mod.build_atlas(paths, symbols, gaps, window_size=32)
            by_name = {row["name"]: row for row in atlas["functions"]}
            self.assertEqual(by_name["A"]["build_matches"]["europe"]["status"], "exact_same_offset")
            self.assertEqual(by_name["B"]["build_matches"]["europe"]["status"], "exact_unique_relocated")
            self.assertEqual(by_name["B"]["build_matches"]["europe"]["file_offset"], moved)
            self.assertEqual(by_name["B"]["build_matches"]["prototype"]["status"], "unmatched")
            self.assertEqual(by_name["A"]["semantic_status"], "corroborated")
            self.assertEqual(by_name["B"]["semantic_status"], "candidate")
            self.assertEqual(atlas["coverage"]["explicit_gap_count"], 1)
            self.assertEqual(atlas["coverage"]["known_function_symbols_atlased"], 2)
            self.assertIn("Comparative Code Atlas", mod.render_markdown(atlas))

    def test_lorom_mapping_and_address_parsing(self) -> None:
        self.assertEqual(mod.parse_cpu_address("02:9A42 (USA)"), 0x029A42)
        self.assertEqual(mod.lorom_cpu_to_file(0x829A42), 0x011A42)
        self.assertIsNone(mod.lorom_cpu_to_file(0x7E0411))
        self.assertEqual(mod.canonical_cpu(mod.file_to_lorom_cpu(0x011A42)), "82:9A42")


if __name__ == "__main__":
    unittest.main()
