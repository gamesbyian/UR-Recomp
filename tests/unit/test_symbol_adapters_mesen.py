from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "export_symbol_adapters", ROOT / "tools" / "export_symbol_adapters.py"
)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class MesenSymbolAdapterTests(unittest.TestCase):
    def test_lorom_function_maps_to_prg_rom_offset(self) -> None:
        rendered = mod.render_mesen([
            {
                "kind": "function",
                "address": "01:B8F1",
                "name": "RNC1_Unpack",
                "notes": "decoder",
            }
        ])
        self.assertIn("SnesPrgRom:B8F1:RNC1_Unpack:decoder\n", rendered)

    def test_wram_banks_map_to_contiguous_work_ram(self) -> None:
        rendered = mod.render_mesen([
            {"kind": "ram", "address": "7E:1234", "name": "Low"},
            {"kind": "ram", "address": "7F:1234", "name": "High"},
        ])
        self.assertIn("SnesWorkRam:1234:Low\n", rendered)
        self.assertIn("SnesWorkRam:11234:High\n", rendered)

    def test_comments_escape_newlines_and_invalid_names_are_omitted(self) -> None:
        rendered = mod.render_mesen([
            {
                "kind": "ram",
                "address": "7E:0001",
                "name": "Good_Name",
                "notes": "line one\nline two",
            },
            {
                "kind": "ram",
                "address": "7E:0002",
                "name": "bad-name",
            },
        ])
        self.assertIn("SnesWorkRam:0001:Good_Name:line one\\nline two\n", rendered)
        self.assertNotIn("bad-name", rendered)


if __name__ == "__main__":
    unittest.main()
