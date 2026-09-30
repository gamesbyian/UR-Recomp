#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/inspect_audio_extended_records.py"
SPEC = importlib.util.spec_from_file_location("inspect_audio_extended_records", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ExtendedAudioRecordTests(unittest.TestCase):
    def test_parses_extended_contiguous_records(self):
        # LoROM CPU 10:8000 maps to file offset 0x080000.
        rom = bytearray(0x90000)
        cursor = 0x080000
        for block_id in range(0x43):
            payload = bytes((block_id, 0x1D, 0x00, 0x00, block_id ^ 0xFF))
            record = (len(payload) + 2).to_bytes(2, "little") + payload
            rom[cursor:cursor + len(record)] = record
            cursor += len(record)

        report = MODULE.build_report(bytes(rom))
        self.assertEqual(report["parsed_record_count"], 0x43)
        self.assertEqual(len(report["records"]), 0x11)
        first = report["records"][0]
        last = report["records"][-1]
        self.assertEqual(first["id_hex"], "0x32")
        self.assertEqual(last["id_hex"], "0x42")
        self.assertEqual(first["first_word_le"], 0x1D32)
        self.assertEqual(last["payload_length"], 5)


if __name__ == "__main__":
    unittest.main()
