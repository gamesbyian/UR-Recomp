from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import trace_apu_ports as apu


class ApuTraceSummaryTests(unittest.TestCase):
    def test_normalize_filters_and_parses_hex_fields(self) -> None:
        raw = [
            {"f": 10, "adr": "2140", "val": "AA"},
            {"f": "11", "adr": "0x2143", "val": "0x05"},
            {"f": 12, "adr": "4200", "val": "80"},
        ]
        events = apu.normalize_events(raw)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["address"], 0x2140)
        self.assertEqual(events[0]["value"], 0xAA)
        self.assertEqual(events[1]["port"], 3)
        self.assertEqual(events[1]["value_hex"], "0x05")

    def test_bursts_split_on_idle_frame_gap(self) -> None:
        events = [
            {"frame": 1, "address_hex": "0x2140", "value_hex": "0x01", "address": 0x2140},
            {"frame": 2, "address_hex": "0x2141", "value_hex": "0x02", "address": 0x2141},
            {"frame": 5, "address_hex": "0x2140", "value_hex": "0x03", "address": 0x2140},
        ]
        bursts = apu.group_bursts(events)
        self.assertEqual(len(bursts), 2)
        self.assertEqual(bursts[0]["event_count"], 2)
        self.assertEqual(bursts[1]["start_frame"], 5)

    def test_summary_counts_ports_and_frame_signatures(self) -> None:
        events = apu.normalize_events(
            [
                {"f": 7, "adr": "2140", "val": "01"},
                {"f": 7, "adr": "2141", "val": "02"},
                {"f": 8, "adr": "2140", "val": "01"},
            ]
        )
        report = apu.summarize(events, race_active_frame=99)
        self.assertEqual(report["event_count"], 3)
        self.assertEqual(report["frames_with_writes"], 2)
        self.assertEqual(report["ports"]["0x2140"]["writes"], 2)
        self.assertEqual(report["ports"]["0x2140"]["unique_values"], 1)
        self.assertEqual(report["race_active_frame"], 99)
        self.assertEqual(
            report["frame_signatures"][0]["writes"],
            ["0x2140=0x01", "0x2141=0x02"],
        )


if __name__ == "__main__":
    unittest.main()
