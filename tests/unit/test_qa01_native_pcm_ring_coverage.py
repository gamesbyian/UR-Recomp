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

    def test_post_wav_census_rejects_second_kon_inside_real_pcm_window(self):
        first = self.report()
        second = self.report(head=3, stats_head=3)
        second['events'] = first['events'] + [
            {'t': 'reg', 'adr': '0x4c', 'val': '0x81', 's': 41000}]
        second['events_returned'] = 2
        with self.assertRaisesRegex(ValueError, 'post-WAV DSP KON history ambiguous'):
            pcm.validate_post_wav_kon_window(
                first, second, kon_sample_index=40000, before=500, after=2000)
        # An event strictly after the captured WAV end cannot change it.
        second['events'][-1]['s'] = 42000
        pcm.validate_post_wav_kon_window(
            first, second, kon_sample_index=40000, before=500, after=2000)

    def test_post_wav_census_rejects_overwrite_regression_and_history_change(self):
        first = self.report()
        for second, reason in (
            (self.report(oldest=1), 'overwritten'),
            (self.report(head=1, stats_head=1), 'counters regressed'),
            (self.report(), 'history changed'),
        ):
            if reason == 'history changed':
                second['events'][0]['s'] = 40001
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                pcm.validate_post_wav_kon_window(
                    first, second, kon_sample_index=40000, before=500, after=2000)

    def test_offline_cli_requires_post_wav_census_before_success_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = root / 'native.exe'
            native.write_bytes(b'fake executable for ROM-free regression')
            wav, receipt = root / 'out.wav', root / 'receipt.json'
            first = self.report()
            second = self.report(head=3, stats_head=3)
            second['events'] = first['events'] + [
                {'t': 'reg', 'adr': '0x4c', 'val': '0x80', 's': 41000}]
            second['events_returned'] = 2
            def fake_wav(*args, **kwargs):
                wav.write_bytes(b'UNQUALIFIED-WAV')
                return {'wav_sha256': '0' * 64, 'sample_frames': 2500,
                        'kon_offset_frames': 500}
            with (mock.patch.object(sys, 'argv', ['pcm', '--kon-sample-index', '40000',
                   '--before', '500', '--after', '2000',
                   '--wav-out', str(wav), '--json-out', str(receipt),
                   '--source-sha', 'a' * 40, '--native-executable', str(native)]),
                  mock.patch.object(pcm, 'connect', return_value=(mock.Mock(), mock.Mock())),
                  mock.patch.object(pcm, 'capture', side_effect=[first, second]) as scans,
                  mock.patch.object(pcm, 'capture_kon_pcm', side_effect=fake_wav),
                  self.assertRaisesRegex(ValueError, 'post-WAV DSP KON history ambiguous')):
                pcm.main()
            self.assertEqual(scans.call_count, 2)
            self.assertTrue(wav.exists())  # Unqualified output is not a receipt.
            self.assertFalse(receipt.exists())

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
