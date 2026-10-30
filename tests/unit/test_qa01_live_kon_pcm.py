"""ROM-free live DSP capture sequencing and false-green controls."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_live_kon_pcm as live


def event(sample):
    return {"s": sample, "t": "reg", "adr": "0x4c", "val": "0x80"}


class Script:
    def __init__(self, pages, produced):
        self.pages = iter(pages)
        self.produced = iter(produced)
        self.first = True
        self.calls = []

    def __call__(self, line):
        self.calls.append(line)
        if line == "audio_stats 0":
            if self.first:
                self.first = False
                return {"event_count": 100, "produced": 0}
            return {"produced": next(self.produced)}
        if line.startswith("audio_events "):
            return next(self.pages)
        raise AssertionError(line)


def page(first, scanned=0, events=(), oldest=0):
    return {"first": first, "scanned": scanned, "oldest": oldest,
            "events": list(events)}


class LiveKONTests(unittest.TestCase):
    def run_watch(self, script, **kw):
        capture = Mock(return_value={"kon_sample_index": 45000, "sample_frames": 2500})
        result = live.watch_first_kon(
            script, wav_path=Path("/tmp/never-written.wav"), before=500,
            after=2000, capacity=65536, timeout=2, interval=.01,
            clock=lambda: 0, sleep=lambda _: None, capture_fn=capture, **kw)
        return result, capture

    def test_live_arm_poll_wait_then_exact_wav_request(self):
        script = Script([page(100, 1, [event(45000)]), page(101)], [45500, 47000])
        result, capture = self.run_watch(script)
        self.assertEqual(result["arm_event_count"], 100)
        self.assertEqual(result["last_scanned_event_count"], 101)
        self.assertEqual(result["retention_margin_frames_before_wav_request"], 63036)
        self.assertFalse(result["target_zoo_command_link_independently_verified"])
        self.assertEqual(capture.call_count, 1)
        self.assertEqual(capture.call_args.kwargs["kon_sample_index"], 45000)

    def test_live_event_ring_gap_fails_before_capture(self):
        script = Script([page(105, oldest=105)], [])
        with self.assertRaisesRegex(ValueError, "overrun"):
            self.run_watch(script)

    def test_multiple_kons_fail_closed(self):
        script = Script([page(100, 2, [event(45000), event(45001)])], [])
        with self.assertRaisesRegex(ValueError, "multiple"):
            self.run_watch(script)

    def test_retention_expired_fails_before_wav(self):
        script = Script([page(100, 1, [event(45000)])], [110536])
        with self.assertRaisesRegex(ValueError, "expired"):
            self.run_watch(script)

    def test_invalid_sample_and_page_fields_fail(self):
        for p in [page(100, 1, [event("45000")]),
                  page(100, scanned=8001), page(100, events=[None])]:
            with self.subTest(page=p), self.assertRaises(ValueError):
                self.run_watch(Script([p], [46000]))

    def test_missing_event_timeout_is_bounded(self):
        ticks = iter([0, 0, 3])
        script = Script([page(100)], [46000])
        with self.assertRaises(TimeoutError):
            live.watch_first_kon(script, wav_path=Path("/tmp/none.wav"),
                                 timeout=2, clock=lambda: next(ticks),
                                 sleep=lambda _: None)

    def test_bad_capacity_and_interval_rejected(self):
        for capacity, interval in [(1, .01), (65536, 0), (65536, 2)]:
            with self.subTest(capacity=capacity, interval=interval), self.assertRaises(ValueError):
                live.watch_first_kon(lambda _: {}, wav_path=Path("/tmp/none.wav"),
                                     capacity=capacity, interval=interval)


if __name__ == "__main__":
    unittest.main()
