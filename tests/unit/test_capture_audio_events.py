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


if __name__ == "__main__":
    unittest.main()
