#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/verify_unused_audio_trace.py"
SPEC = importlib.util.spec_from_file_location("verify_unused_audio_trace", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class UnusedAudioTraceVerifierTests(unittest.TestCase):
    def synthetic_rom(self, selector=0x3B):
        rom = bytearray(0x0B0000)
        cursor = 0x080000
        for block_id in range(selector + 1):
            if block_id == selector:
                payload = bytes.fromhex("00 04 00 1d") + bytes(range(64))
            else:
                payload = bytes([block_id & 0xFF]) * 40
            record = (len(payload) + 2).to_bytes(2, "little") + payload
            rom[cursor:cursor + len(record)] = record
            cursor += len(record)
        return bytes(rom)

    def test_finds_exact_song_body_among_port3_bytes(self):
        rom = self.synthetic_rom()
        body = bytes(range(64))
        stream = b"prefix" + body + b"suffix"
        events = [
            {"address": 0x2142, "value": 0x80},
            *[{"address": 0x2143, "value": b} for b in stream],
        ]
        report = MODULE.verify(rom, {"events": events}, 0x3B)
        self.assertTrue(report["exact_body_found"])
        self.assertEqual(report["match_offset"], len(b"prefix"))
        self.assertEqual(report["expected_body_length"], 64)

    def test_rejects_missing_body(self):
        rom = self.synthetic_rom()
        events = [{"address_hex": "0x2143", "value_hex": "0xAA"}] * 100
        report = MODULE.verify(rom, {"events": events}, 0x3B)
        self.assertFalse(report["exact_body_found"])

    def test_counter_segments_split_on_counter_discontinuity(self):
        events = [
            {"address": 0x2143, "value": 0x10},
            {"address": 0x2142, "value": 0xFE},
            {"address": 0x2143, "value": 0x11},
            {"address": 0x2142, "value": 0xFF},
            {"address": 0x2143, "value": 0x12},
            {"address": 0x2142, "value": 0x00},
            {"address": 0x2142, "value": 0x7A},
            {"address": 0x2143, "value": 0x20},
            {"address": 0x2142, "value": 0x80},
        ]
        segments, anomalies = MODULE.counter_segments({"events": events})
        self.assertEqual(segments, [bytes([0x10, 0x11, 0x12]), bytes([0x20])])
        self.assertEqual(len(anomalies), 1)



if __name__ == "__main__":
    unittest.main()
