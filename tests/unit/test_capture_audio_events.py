from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import capture_audio_events as cap


class AudioEventCaptureTests(unittest.TestCase):
    def test_pages_until_short_scan(self) -> None:
        calls = []
        responses = [
            {"events": [{"t": "cpu_wr"}], "scanned": 2, "first": 0, "oldest": 0},
            {"events": [{"t": "spc_rd"}], "scanned": 1, "first": 2, "oldest": 0},
        ]

        def command(line: str) -> dict:
            calls.append(line)
            return responses.pop(0)

        events, meta = cap.page_events(
            command,
            first=0,
            page_size=2,
            event_filter=0,
        )
        self.assertEqual([e["t"] for e in events], ["cpu_wr", "spc_rd"])
        self.assertEqual(
            calls,
            ["audio_events 0 2 0", "audio_events 2 2 0"],
        )
        self.assertEqual(meta["oldest"], 0)
        self.assertEqual(meta["_client_scan_end"], 3)
        self.assertTrue(meta["_client_contiguous"])

    def test_noncontiguous_page_is_flagged_for_strict_consumers(self) -> None:
        def command(line: str) -> dict:
            self.assertEqual(line, 'audio_events 0 8 1')
            return {'events': [{'t': 'reg'}], 'scanned': 1,
                    'first': 3, 'oldest': 3}

        _, meta = cap.page_events(command, first=0, page_size=8, event_filter=1)
        self.assertFalse(meta['_client_contiguous'])
        self.assertEqual(meta['_client_scan_end'], 4)

    def test_capture_includes_stats_and_ring_metadata(self) -> None:
        responses = {
            "audio_stats 5": {"event_count": 3, "cpu_port_writes": 1},
            "audio_events 0 8 2": {
                "events": [{"t": "cpu_wr", "adr": "0x02", "val": "0x31"}],
                "scanned": 1,
                "first": 0,
                "oldest": 0,
            },
        }

        def command(line: str) -> dict:
            return responses[line]

        report = cap.capture(command, page_size=8, event_filter=2)
        self.assertEqual(report["event_head"], 3)
        self.assertEqual(report["events_returned"], 1)
        self.assertEqual(report["event_filter"], 2)
        self.assertEqual(report["stats"]["cpu_port_writes"], 1)
        self.assertEqual(report["last_scanned_event_index"], 1)
        self.assertTrue(report["event_pages_contiguous"])


if __name__ == "__main__":
    unittest.main()
