from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import trace_audio_source_table as ast


class AudioSourceTableTraceTests(unittest.TestCase):
    def test_generated_variant_name(self) -> None:
        self.assertEqual(
            ast.generated_variant_name(0x828298, 1, 0),
            "bank_82_8298_M1X0",
        )

    def test_generated_variant_name_low_mirror(self) -> None:
        self.assertEqual(
            ast.generated_variant_name(0x028298, 1, 0),
            "bank_02_8298_M1X0",
        )

    def test_lorom_file_offset_high_half(self) -> None:
        self.assertEqual(ast.lorom_file_offset(0x828298), 0x010298)
        self.assertEqual(ast.lorom_file_offset(0x028298), 0x010298)
        self.assertIsNone(ast.lorom_file_offset(0x820123))

    def test_source_pointer_from_snapshot_with_zero_direct_page(self) -> None:
        blob = bytearray(0x80)
        start = 0x40
        ptr_addr = 0x63
        rel = ptr_addr - start
        blob[rel:rel + 3] = bytes([0x34, 0x92, 0x8A])
        self.assertEqual(
            ast.direct_page_pointer_from_snapshot(bytes(blob), start, 0, 0x63),
            0x8A9234,
        )

    def test_source_pointer_respects_nonzero_direct_page(self) -> None:
        blob = bytearray(0x80)
        start = 0x140
        ptr_addr = 0x163
        rel = ptr_addr - start
        blob[rel:rel + 3] = bytes([0x00, 0x80, 0x83])
        self.assertEqual(
            ast.direct_page_pointer_from_snapshot(bytes(blob), start, 0x100, 0x63),
            0x838000,
        )

    def test_source_pointer_returns_none_outside_snapshot(self) -> None:
        self.assertIsNone(
            ast.direct_page_pointer_from_snapshot(bytes(16), 0x100, 0, 0x63)
        )

    def test_entry_pointer_reads_direct_page_zero(self) -> None:
        blob = bytearray(0x100)
        blob[0:3] = bytes([0x00, 0x80, 0x8C])
        self.assertEqual(
            ast.direct_page_pointer_from_snapshot(bytes(blob), 0, 0, 0x00),
            0x8C8000,
        )

    def test_parse_blob_hex_accepts_compact_or_spaced(self) -> None:
        self.assertEqual(ast.parse_blob_hex("0011aaff"), bytes.fromhex("00 11 aa ff"))
        self.assertEqual(ast.parse_blob_hex("00 11 aa ff"), bytes.fromhex("00 11 aa ff"))


if __name__ == "__main__":
    unittest.main()
