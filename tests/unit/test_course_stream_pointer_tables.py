#!/usr/bin/env python3
"""Regression tests for course RNC pointer-table search helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from find_course_stream_pointer_tables import encodings, find_runs, lorom24, occurrences


class CoursePointerSearchTests(unittest.TestCase):
    def test_lorom_encoding(self):
        # File offset 0x0C0000 is LoROM bank $18:$8000.
        self.assertEqual(lorom24(0x0C0000), 0x188000)
        e = encodings(0x0C0183, 0x0C0000)
        self.assertEqual(e["lorom24_le"], bytes.fromhex("83 81 18"))
        self.assertEqual(e["file24_le"], bytes.fromhex("83 01 0c"))
        self.assertEqual(e["corpus_rel24_le"], bytes.fromhex("83 01 00"))

    def test_consecutive_descriptor_run(self):
        data = bytearray(128)
        needles = [bytes([0xA0+i, 0xB0+i, 0xC0+i]) for i in range(5)]
        base = 17
        stride = 6
        for i, needle in enumerate(needles):
            pos = base + i * stride
            data[pos:pos+3] = needle
        per = [occurrences(bytes(data), n) for n in needles]
        runs = find_runs(per, stride)
        self.assertTrue(runs)
        self.assertEqual(runs[0]["first_stream"], 1)
        self.assertEqual(runs[0]["last_stream"], 5)
        self.assertEqual(runs[0]["length"], 5)
        self.assertEqual(runs[0]["rom_offset"], base)

    def test_noise_does_not_make_ordered_run(self):
        data = bytes.fromhex("01 02 03 00 04 05 06 00 07 08 09")
        needles = [bytes.fromhex("01 02 03"), bytes.fromhex("07 08 09"), bytes.fromhex("04 05 06")]
        per = [occurrences(data, n) for n in needles]
        self.assertEqual(find_runs(per, 4), [])


if __name__ == "__main__":
    unittest.main()
