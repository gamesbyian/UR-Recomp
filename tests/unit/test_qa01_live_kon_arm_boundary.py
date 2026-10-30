"""Reject a first-after-arm KON whose PCM window may contain unobserved earlier KON."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import qa01_live_kon_pcm as live


class Script:
    def __init__(self, armed_produced):
        self.armed_produced = armed_produced
        self.stats_calls = 0

    def __call__(self, line):
        if line == 'audio_stats 0':
            self.stats_calls += 1
            if self.stats_calls == 1:
                return {'event_count': 100, 'produced': self.armed_produced}
            return {'event_count': 101, 'produced': 47000}
        if line == 'audio_events 100 8000 1':
            return {'first': 100, 'oldest': 0, 'scanned': 1,
                    'events': [{'t': 'reg', 'adr': '0x4c', 'val': '0x80', 's': 45000}]}
        raise AssertionError(line)


class ArmBoundaryTests(unittest.TestCase):
    def run_case(self, armed_produced):
        capture = Mock(return_value={'kon_sample_index': 45000, 'sample_frames': 2500})
        def watcher():
            return live.watch_first_kon(
                Script(armed_produced), wav_path=Path('/tmp/not-written.wav'),
                before=500, after=2000, capacity=65536, timeout=2,
                interval=.01, clock=lambda: 0, sleep=lambda _: None,
                capture_fn=capture)
        return watcher, capture

    def test_pre_arm_audio_overlap_is_rejected_without_wav(self):
        # Earlier unobserved KON at 44600 would lie inside [44500, 47000).
        watcher, capture = self.run_case(44750)
        with self.assertRaisesRegex(ValueError, 'predates live arm'):
            watcher()
        capture.assert_not_called()

    def test_exact_start_at_arm_is_rejected(self):
        # Pre-arm event #99 can be voice-7 KON at sample index 44500.
        # It is skipped by the arm event cursor but its first PCM sample
        # lies in the selected [44500, 47000) window.
        watcher, capture = self.run_case(44500)
        with self.assertRaisesRegex(ValueError, 'touches its sample boundary'):
            watcher()
        capture.assert_not_called()

    def test_strictly_after_arm_is_allowed(self):
        watcher, capture = self.run_case(44499)
        result = watcher()
        self.assertEqual(result['arm_produced_samples'], 44499)
        self.assertEqual(result['kon_sample_index'], 45000)
        capture.assert_called_once()

    def test_invalid_arm_sample_counter_rejected(self):
        for value in (None, -1, '44500', True):
            with self.subTest(value=value):
                watcher, capture = self.run_case(value)
                with self.assertRaisesRegex(ValueError, 'arm produced samples'):
                    watcher()
                capture.assert_not_called()


if __name__ == '__main__':
    unittest.main()
