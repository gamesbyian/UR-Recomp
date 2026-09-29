from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import inspect_spc_upload_stream as spc


class SpcUploadStreamTests(unittest.TestCase):
    def test_parses_blocks_and_terminator(self) -> None:
        payload1 = bytes([1, 2, 3])
        payload2 = bytes([0xAA, 0xBB])
        data = (
            bytes([3, 0, 0x00, 0x30])
            + payload1
            + bytes([2, 0, 0x10, 0x40])
            + payload2
            + bytes([0, 0, 0x34, 0x12])
        )
        report = spc.parse_stream(data)
        self.assertTrue(report["complete"])
        self.assertEqual(report["stop_reason"], "terminator")
        self.assertEqual(len(report["blocks"]), 2)
        self.assertEqual(report["blocks"][0]["target"], 0x3000)
        self.assertEqual(report["blocks"][0]["length"], 3)
        self.assertEqual(
            report["blocks"][0]["payload_sha256"],
            hashlib.sha256(payload1).hexdigest(),
        )
        self.assertEqual(report["blocks"][1]["target"], 0x4010)
        self.assertEqual(report["terminator"]["target_final_pc"], 0x1234)

    def test_reports_truncated_payload(self) -> None:
        data = bytes([5, 0, 0x00, 0x30, 1, 2])
        report = spc.parse_stream(data)
        self.assertFalse(report["complete"])
        self.assertEqual(report["stop_reason"], "truncated_payload")
        self.assertEqual(report["blocks"][0]["available_payload_bytes"], 2)
        self.assertFalse(report["blocks"][0]["payload_complete"])

    def test_reports_truncated_header(self) -> None:
        report = spc.parse_stream(bytes([1, 2, 3]))
        self.assertFalse(report["complete"])
        self.assertEqual(report["stop_reason"], "truncated_header")

    def test_honors_nonzero_start(self) -> None:
        data = b"xxxx" + bytes([1, 0, 0x20, 0x30, 0x55, 0, 0, 0x78, 0x56])
        report = spc.parse_stream(data, start=4)
        self.assertEqual(report["blocks"][0]["header_offset"], 4)
        self.assertEqual(report["blocks"][0]["target"], 0x3020)
        self.assertEqual(report["terminator"]["target_final_pc"], 0x5678)


if __name__ == "__main__":
    unittest.main()
