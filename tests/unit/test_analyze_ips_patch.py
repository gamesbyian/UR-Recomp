from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import analyze_ips_patch as ips


def make_patch(*parts: bytes, truncate_to: int | None = None) -> bytes:
    data = bytearray(b"PATCH")
    for part in parts:
        data.extend(part)
    data.extend(b"EOF")
    if truncate_to is not None:
        data.extend(truncate_to.to_bytes(3, "big"))
    return bytes(data)


def literal(offset: int, payload: bytes) -> bytes:
    return offset.to_bytes(3, "big") + len(payload).to_bytes(2, "big") + payload


def rle(offset: int, length: int, value: int) -> bytes:
    return (
        offset.to_bytes(3, "big")
        + b"\x00\x00"
        + length.to_bytes(2, "big")
        + bytes([value])
    )


class ParseIpsTests(unittest.TestCase):
    def test_literal_and_rle_records(self) -> None:
        patch = make_patch(literal(0x1234, b"\xAA\xBB\xCC"), rle(0x8000, 4, 0x7F))
        records, truncate_to = ips.parse_ips(patch)
        self.assertIsNone(truncate_to)
        self.assertEqual(
            [(r.offset, r.data, r.encoding) for r in records],
            [
                (0x1234, b"\xAA\xBB\xCC", "literal"),
                (0x8000, b"\x7F" * 4, "rle"),
            ],
        )

    def test_rejects_truncated_patch(self) -> None:
        with self.assertRaises(ValueError):
            ips.parse_ips(b"PATCH\x00\x00")

    def test_optional_truncate_size(self) -> None:
        records, truncate_to = ips.parse_ips(make_patch(truncate_to=0x123456))
        self.assertEqual(records, [])
        self.assertEqual(truncate_to, 0x123456)


class AnalysisTests(unittest.TestCase):
    def test_coalesces_overlapping_and_adjacent_ranges(self) -> None:
        records = [
            ips.IpsRecord(10, b"abc", "literal"),
            ips.IpsRecord(13, b"de", "literal"),
            ips.IpsRecord(12, b"zz", "literal"),
            ips.IpsRecord(20, b"x", "literal"),
        ]
        self.assertEqual(ips.coalesce_ranges(records), [(10, 15), (20, 21)])

    def test_lorom_mapping(self) -> None:
        self.assertEqual(ips.lorom_cpu_address(0x01534C), "82:D34C")
        self.assertEqual(ips.lorom_cpu_address(0x000200, 512), "80:8000")
        self.assertIsNone(ips.lorom_cpu_address(0x000100, 512))

    def test_base_analysis_reports_actual_changes(self) -> None:
        base = bytes([0x00]) * 0x10000
        patch = make_patch(literal(0x10, b"\x00\x01"), rle(0x20, 3, 0x02))
        report = ips.analyze_patch(patch, base=base)
        self.assertEqual(report["encoded_write_bytes"], 5)
        self.assertEqual(report["result"]["actual_changed_bytes"], 4)
        self.assertEqual(report["ranges"][0]["start_hex"], "0x000010")
        self.assertEqual(report["ranges"][0]["lorom_start"], "80:8010")
        self.assertEqual(report["records"][0]["actual_changed_bytes"], 1)
        self.assertEqual(report["records"][0]["before_hex"], "0000")
        self.assertEqual(report["records"][0]["after_hex"], "0001")
        self.assertEqual(report["records"][1]["before_ascii"], "...")
        self.assertEqual(report["records"][1]["after_ascii"], "...")
        self.assertEqual(report["records"][1]["after_printable_ratio"], 0.0)

    def test_apply_can_extend_and_truncate(self) -> None:
        patch = make_patch(literal(6, b"xy"), truncate_to=7)
        records, truncate_to = ips.parse_ips(patch)
        self.assertEqual(ips.apply_records(b"abcd", records, truncate_to), b"abcd\x00\x00x")


if __name__ == "__main__":
    unittest.main()
