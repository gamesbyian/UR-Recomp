"""Later KON events beyond the exclusive WAV end must not spoil first-KON PCM."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_live_kon_pcm as live


def kon(sample: int, value: str = "0x80") -> dict:
    return {"t": "reg", "adr": "0x4c", "val": value, "s": sample}


class Server:
    def __init__(self, *, second_sample: int, during_wav: bool, second_value: str = "0x80"):
        self.second_sample = second_sample
        self.second_value = second_value
        self.during_wav = during_wav
        self.armed = False
        self.head = 101 if during_wav else 102
        self.produced = 47000 if during_wav else 48000
        self.calls = []

    def __call__(self, line: str) -> dict:
        self.calls.append(line)
        if line == "audio_stats 0":
            if not self.armed:
                self.armed = True
                return {"event_count": 100, "produced": 0}
            return {"event_count": self.head, "produced": self.produced}
        if line == "audio_events 100 8000 1":
            events = [kon(45000)]
            if not self.during_wav:
                events.append(kon(self.second_sample, self.second_value))
            return {"first": 100, "oldest": 0,
                    "scanned": len(events), "events": events}
        if line == "audio_events 101 1 1" and self.during_wav:
            return {"first": 101, "oldest": 0,
                    "scanned": 1, "events": [kon(self.second_sample, self.second_value)]}
        raise AssertionError(f"unexpected debug command: {line}")


class PostWindowKONTests(unittest.TestCase):
    def run_case(self, sample: int, *, during_wav: bool, second_value: str = "0x80"):
        server = Server(second_sample=sample, during_wav=during_wav, second_value=second_value)

        def capture(*_args, **_kwargs):
            if during_wav:
                server.head = 102
                server.produced = 48000
            return {"kon_sample_index": 45000, "sample_frames": 2500}

        capture_fn = Mock(side_effect=capture)
        def watch():
            return live.watch_first_kon(
                server, wav_path=Path("/tmp/unused-kon.wav"),
                before=500, after=2000, capacity=65536,
                timeout=2, interval=.01, clock=lambda: 0,
                sleep=lambda _: None, capture_fn=capture_fn)
        return watch, capture_fn, server

    def test_second_kon_at_exclusive_wav_end_is_not_ambiguous(self):
        # The selected WAV covers [44500, 47000); a later KON at 47000
        # cannot alter any sample inside that retained PCM window.
        for during_wav in (False, True):
            with self.subTest(during_wav=during_wav):
                watch, capture_fn, server = self.run_case(47000, during_wav=during_wav)
                result = watch()
                self.assertEqual(result["kon_sample_index"], 45000)
                capture_fn.assert_called_once()
                if during_wav:
                    self.assertIn("audio_events 101 1 1", server.calls)

    def test_later_combined_bitmask_outside_wav_is_irrelevant(self):
        # $4C=$81 still keys voice 7, but cannot alter [44500,47000)
        # when it occurs at the exclusive end. Check both race phases.
        for during_wav in (False, True):
            with self.subTest(during_wav=during_wav):
                watch, capture_fn, _ = self.run_case(
                    47000, during_wav=during_wav, second_value="0x81")
                result = watch()
                self.assertEqual(result["kon_sample_index"], 45000)
                capture_fn.assert_called_once()

    def test_combined_bitmask_inside_wav_still_fails_closed(self):
        for during_wav in (False, True):
            with self.subTest(during_wav=during_wav):
                watch, capture_fn, _ = self.run_case(
                    46999, during_wav=during_wav, second_value="0x81")
                with self.assertRaisesRegex(ValueError, "combined voice-7 KON"):
                    watch()
                self.assertEqual(capture_fn.call_count, 1 if during_wav else 0)

    def test_second_kon_inside_wav_window_still_fails_closed(self):
        for during_wav in (False, True):
            with self.subTest(during_wav=during_wav):
                watch, capture_fn, _ = self.run_case(46999, during_wav=during_wav)
                with self.assertRaisesRegex(ValueError, "multiple voice-7 KON"):
                    watch()
                self.assertEqual(capture_fn.call_count, 1 if during_wav else 0)


if __name__ == "__main__":
    unittest.main()
