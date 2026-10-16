"""Bounded exact PE source-epoch read-only diagnostics; never mutate binary."""
from __future__ import annotations

import sys
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_windows_pe_timestamp as pe

EPOCH = 1792100000


def fixture(*, coff=EPOCH, debug=EPOCH) -> bytearray:
    data = bytearray(2048)
    data[:2] = b"MZ"
    address = 0x80
    struct.pack_into("<I", data, 0x3C, address)
    data[address:address+4] = b"PE\x00\x00"
    struct.pack_into("<HHI", data, address+4, pe.AMD64, 1, coff)
    struct.pack_into("<H", data, address+20, 0xF0)
    optional = address + 24
    struct.pack_into("<H", data, optional, pe.PE32PLUS_MAGIC)
    struct.pack_into("<II", data, optional+112+6*8, 0x2010, 28)
    section = optional + 0xF0
    struct.pack_into("<IIII", data, section+8, 0x200, 0x2000, 0x200, 0x200)
    struct.pack_into("<I", data, 0x210 + 4, debug)
    return data


class WindowsPETimestampContract(unittest.TestCase):
    def test_matching_coff_and_mapped_debug_directory_source_epoch(self):
        data = fixture()
        before = bytes(data)
        result = pe.inspect(data, EPOCH)
        self.assertEqual(result["source_date_epoch"], EPOCH)
        self.assertTrue(result["real_pe32plus_amd64"])
        self.assertEqual(result["coff_timestamp_file_offset"], 0x88)
        self.assertEqual(result["debug_timestamps"], [
            {"file_offset": 0x214, "value": EPOCH}])
        self.assertFalse(result["post_link_bytes_modified"])
        self.assertEqual(result["release_gate_credit"], 0)
        self.assertEqual(bytes(data), before)

    def test_live_wall_clock_coff_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "COFF TimeDateStamp"):
            pe.inspect(fixture(coff=EPOCH + 10), EPOCH)

    def test_mismatched_debug_directory_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "debug-directory TimeDateStamp"):
            pe.inspect(fixture(debug=EPOCH + 10), EPOCH)

    def test_tampered_debug_rva_missing_directory_and_truncation_rejected(self):
        cases = [
            ("debug directory", lambda x: struct.pack_into(
                "<II", x, 0x98+112+6*8, 0, 0)),
            ("RVA", lambda x: struct.pack_into(
                "<II", x, 0x98+112+6*8, 0x505050, 28)),
            ("extends beyond", lambda x: struct.pack_into(
                "<II", x, 0x98+112+6*8, 0x21F0, 28)),
            ("optional header", lambda x: struct.pack_into(
                "<H", x, 0x80+20, 8)),
        ]
        for fragment, tamper in cases:
            with self.subTest(fragment=fragment):
                data = fixture()
                tamper(data)
                with self.assertRaisesRegex(ValueError, fragment):
                    pe.inspect(data, EPOCH)

    def test_refuse_bad_architecture_invalid_epoch_and_non_pe(self):
        with self.assertRaisesRegex(ValueError, "source epoch"):
            pe.inspect(fixture(), 0)
        with self.assertRaisesRegex(ValueError, "PE signature"):
            data = fixture()
            data[0x80:0x84] = b"NOPE"
            pe.inspect(data, EPOCH)
        data = fixture()
        struct.pack_into("<H", data, 0x84, 0x14C)
        with self.assertRaisesRegex(ValueError, "AMD64"):
            pe.inspect(data, EPOCH)

    def test_workflow_pins_compiler_and_source_commit_timestamp(self):
        source = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml"
                  ).read_text(encoding="utf-8")
        self.assertIn("--artifact windows-x64 --tag v1.0.14", source)
        self.assertIn("SOURCE_DATE_EPOCH", source)
        self.assertIn('git show -s --format=%ct "$GITHUB_SHA"', source)
        self.assertIn("python tools/check_windows_pe_timestamp.py", source)
        self.assertIn("python tests/unit/test_check_windows_pe_timestamp.py", source)
        self.assertIn("22.1.8", source)


if __name__ == "__main__":
    unittest.main()
