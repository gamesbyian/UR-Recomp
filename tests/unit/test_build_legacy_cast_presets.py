import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import build_legacy_cast_presets as cast  # noqa: E402


class LegacyCastPresetTests(unittest.TestCase):
    def test_palette_asset_reads_five_byte_table_entry(self) -> None:
        rom = bytearray(0x30000)
        table = cast.lorom(0x82, 0xB32F)
        entry = table + 5 * 0x06
        rom[entry:entry + 5] = bytes([0x04, 0x80, 0x81, 0x04, 0x00])  # 04:8180, 4 bytes
        data = cast.lorom(0x04, 0x8180)
        rom[data:data + 4] = bytes([0x8C, 0x31, 0x98, 0x08])
        asset = cast.palette_asset(bytes(rom), 0x06)
        self.assertEqual(asset["source_snes"], "04:8180")
        self.assertEqual(asset["table_entry_snes"], "82:B34D")
        self.assertEqual(asset["bgr555_words"], ["0x318C", "0x0898"])

    def test_colour_labels(self) -> None:
        self.assertEqual(cast.colour_label(0x0898), "red")     # MIKE mid-ramp
        self.assertEqual(cast.colour_label(0x6062), "blue")    # ANDREW
        self.assertEqual(cast.colour_label(0x0337), "yellow")  # MELISSA
        self.assertEqual(cast.colour_label(0x6318), "white")   # DAVE
        self.assertEqual(cast.colour_label(0x423B), "pink")    # CAROL

    def test_grid_rule_confirmations(self) -> None:
        for (row, column), index in cast.CONFIRMED_INDICES.items():
            self.assertEqual(2 * row + column, index)


if __name__ == "__main__":
    unittest.main()
