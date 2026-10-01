from pathlib import Path
import unittest

from tools.analyze_canoe_ips import analyze, parse_ips


ROOT = Path(__file__).resolve().parents[2]


class CanoeIpsTests(unittest.TestCase):
    def test_literal_and_rle_records(self):
        patch = (
            b"PATCH"
            + bytes.fromhex("000010 0002 AA BB")
            + bytes.fromhex("000020 0000 0003 CC")
            + b"EOF"
        )
        rows = parse_ips(patch)
        self.assertEqual(rows[0]["data_hex"], "aa bb")
        self.assertEqual(rows[1]["data_hex"], "cc cc cc")

    def test_optional_rom_comparison_and_lorom_mapping(self):
        patch = b"PATCH" + bytes.fromhex("01534C 0002 22 00") + b"EOF"
        rom = bytearray(0x200000)
        rom[0x1534C:0x1534E] = b"\x12\x34"
        report = analyze(patch, bytes(rom))
        row = report["records"][0]
        self.assertEqual(row["lorom_cpu"], "02:D34C")
        self.assertEqual(row["original_hex"], "12 34")
        self.assertNotIn("semantic_summary", report)

    def test_recovered_patch_semantics(self):
        patch = (ROOT / "reference/imported/patches/uniracers_canoe.ips").read_bytes()
        rom = (ROOT / "reference/roms/retail/Uniracers_USA.sfc").read_bytes()
        report = analyze(patch, rom)
        summary = report["semantic_summary"]

        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["record_count"], 7)
        self.assertEqual(summary["checksum"]["sum"], "FFFF")
        self.assertEqual(
            [(h["site"], h["target"]) for h in summary["hooks"]],
            [("02:D34C", "BF:FF00"), ("02:D714", "BF:FF36")],
        )
        self.assertEqual(
            summary["forced_branch"],
            {
                "site": "03:8B16",
                "original": "BEQ +0x04",
                "patched": "BRA +0x04",
            },
        )
        self.assertEqual(
            [r["original_target"] for r in summary["long_store_redirects"]],
            ["7E:2065", "7E:2069"],
        )
        self.assertEqual(
            [r["patched_target"] for r in summary["long_store_redirects"]],
            ["7F:FFE1", "7F:FFEB"],
        )

        handler = summary["injected_handler"]
        self.assertEqual(handler["size"], 230)
        self.assertEqual(
            handler["oam_wrapper"]["dynamic_table_targets"],
            ["7F:FFF1", "7F:FFF4"],
        )
        self.assertEqual(
            handler["hdma_setup"]["channel7"]["table"],
            [
                {"control": 0x6F, "line_count": 0x6F, "repeat": False, "data_hex": "0f 83 0c 01"},
                {"control": 0x02, "line_count": 0x02, "repeat": False, "data_hex": "80 83 0c 01"},
                {"control": 0x60, "line_count": 0x60, "repeat": False, "data_hex": "0f 83 0c 01"},
                {"control": 0, "terminator": True},
            ],
        )
        self.assertEqual(
            handler["hdma_setup"]["channel1"]["table"],
            [
                {"control": 0x70, "line_count": 0x70, "repeat": False, "data_hex": "55 55"},
                {"control": 0x70, "line_count": 0x70, "repeat": False, "data_hex": "55 55"},
                {"control": 0, "terminator": True},
            ],
        )

    def test_rejects_trailing_bytes(self):
        with self.assertRaises(ValueError):
            parse_ips(b"PATCHEOFx")


if __name__ == "__main__":
    unittest.main()
