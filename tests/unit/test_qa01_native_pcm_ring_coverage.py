"""Offline native KON evidence must not silently accept an overwritten DSP event ring."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import qa01_native_pcm_at_kon as pcm


class NativeRingCoverageTests(unittest.TestCase):
    @staticmethod
    def report(oldest=0, head=2, stats_head=2):
        events = [{'t': 'reg', 'adr': '0x4c', 'val': '0x80', 's': 40000}]
        return {'oldest_available': oldest, 'event_head': head,
                'stats': {'event_count': stats_head, 'produced': 45000},
                'events': events, 'events_returned': len(events),
                'last_scanned_event_index': head, 'event_pages_contiguous': True}

    def test_complete_ring_census_is_allowed(self):
        pcm.validate_event_ring_coverage(self.report())

    def test_overwritten_ring_rejected(self):
        with self.assertRaisesRegex(ValueError, 'overwritten'):
            pcm.validate_event_ring_coverage(self.report(oldest=1))

    def test_malformed_counters_rejected(self):
        for changes in ({'oldest': True}, {'oldest': -1},
                        {'head': '2'}, {'stats_head': 3}):
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, 'counters'):
                pcm.validate_event_ring_coverage(self.report(**changes))

    def test_inconsistent_event_census_rejected(self):
        report = self.report()
        report['events_returned'] = 0
        with self.assertRaisesRegex(ValueError, 'census'):
            pcm.validate_event_ring_coverage(report)

    def test_partial_or_discontinuous_scan_rejected(self):
        for changes in ({'last_scanned_event_index': 1},
                        {'event_pages_contiguous': False},
                        {'last_scanned_event_index': None}):
            with self.subTest(changes=changes):
                report = self.report(head=100, stats_head=100)
                report.update(changes)
                with self.assertRaisesRegex(ValueError, 'incomplete or discontinuous'):
                    pcm.validate_event_ring_coverage(report)

    def test_cli_refuses_overwritten_ring_before_wav(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = root / 'native.exe'
            native.write_bytes(b'fake executable for ROM-free test')
            wav, receipt = root / 'out.wav', root / 'receipt.json'
            with (mock.patch.object(sys, 'argv', ['pcm', '--kon-sample-index', '40000',
                   '--wav-out', str(wav), '--json-out', str(receipt),
                   '--source-sha', 'a' * 40, '--native-executable', str(native)]),
                  mock.patch.object(pcm, 'connect', return_value=(mock.Mock(), mock.Mock())),
                  mock.patch.object(pcm, 'capture', return_value=self.report(oldest=5)),
                  mock.patch.object(pcm, 'command', side_effect=AssertionError('must not write WAV')),
                  self.assertRaisesRegex(ValueError, 'overwritten')):
                pcm.main()
            self.assertFalse(wav.exists())
            self.assertFalse(receipt.exists())


if __name__ == '__main__':
    unittest.main()
