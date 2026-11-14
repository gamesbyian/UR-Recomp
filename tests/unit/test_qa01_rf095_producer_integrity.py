"""RF095 rejects incomplete native frame synchronization and extra WAV bytes."""
from __future__ import annotations

import importlib.util
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
import wave
from unittest import mock

ROOT = Path(__file__).resolve().parents[2] / 'tools'


def load_receipt():
    spec = importlib.util.spec_from_file_location('qa01_rf095_pcm_receipt',
                                                  ROOT / 'qa01_rf095_pcm_receipt.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProducerIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        d = Path(self.temp.name)
        self.wav = d / 'ref.wav'
        self.ref_map = d / 'ref.csv'
        self.pcm = d / 'native.pcm'
        self.native_map = d / 'native.csv'
        self.ref_log = d / 'reference.log'
        self.native_log = d / 'native.log'
        with wave.open(str(self.wav), 'wb') as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(32040)
            w.writeframes(struct.pack('<hh', 123, -45) * (6445 + 9 * 128))
        self.ref_map.write_text('frame,samples\n' +
                                ''.join(f'{f},{f if f <= 6445 else 6445 + (f-6445)*128}\n' for f in range(6455)))
        self.pcm.write_bytes(struct.pack('<hh', 12, -8) * (10 * 128))
        self.native_map.write_text('frame,samples\n' +
                                   ''.join(f'{f},{(f - 6447)*128}\n'
                                           for f in range(6447, 6458)))
        self.ref_log.write_text('original replay\n')
        self.native_log.write_text('native replay\n')
        self.receipt = load_receipt()

    def analyze(self):
        return self.receipt.analyze(self.wav, self.ref_map, self.pcm,
                                    self.native_map, self.ref_log, self.native_log)

    def test_normal_complete_producers_are_accepted_as_diagnostics(self):
        result = self.analyze()
        self.assertEqual(result['original']['frames'], 896)
        self.assertEqual(result['native']['frames'], 1280)
        self.assertFalse(result['audible_parity_proven'])


    def test_clean_producer_logs_have_distinct_receipt_identities(self):
        before = self.analyze()
        self.assertEqual(before['producer_logs']['original']['bytes'],
                         len(self.ref_log.read_bytes()))
        self.assertEqual(before['producer_logs']['native']['sha256'],
                         hashlib.sha256(self.native_log.read_bytes()).hexdigest())
        self.native_log.write_text('native replay with additional clean line\n')
        after = self.analyze()
        self.assertNotEqual(before['producer_logs']['native']['sha256'],
                            after['producer_logs']['native']['sha256'])
        self.assertEqual(before['producer_logs']['original'],
                         after['producer_logs']['original'])
        self.assertEqual(before['native']['raw_sha256'],
                         after['native']['raw_sha256'])
        self.ref_log.write_text('different clean original replay\n')
        changed_original = self.analyze()
        self.assertNotEqual(after['producer_logs']['original']['sha256'],
                            changed_original['producer_logs']['original']['sha256'])

    def test_native_pcm_mutation_after_snapshot_cannot_relabel_receipt(self):
        expected = hashlib.sha256(self.pcm.read_bytes()).hexdigest()
        real_map = self.receipt.frame_map
        altered = False

        def mutate_after_snapshot(*args, **kwargs):
            nonlocal altered
            if not altered:
                altered = True
                self.pcm.write_bytes(struct.pack('<hh', 99, -88) * (10 * 128))
            return real_map(*args, **kwargs)

        with mock.patch.object(self.receipt, 'frame_map',
                               side_effect=mutate_after_snapshot):
            result = self.analyze()
        self.assertTrue(altered)
        self.assertEqual(result['native']['raw_sha256'], expected)
        self.assertEqual(result['native']['sha256'], expected)
        self.assertNotEqual(hashlib.sha256(self.pcm.read_bytes()).hexdigest(),
                            expected)

    def test_original_map_mutation_after_snapshot_cannot_relabel_receipt(self):
        expected = hashlib.sha256(self.ref_map.read_bytes()).hexdigest()
        real_map = self.receipt.frame_map
        altered = False

        def mutate_after_snapshot(*args, **kwargs):
            nonlocal altered
            if not altered:
                altered = True
                self.ref_map.write_bytes(self.ref_map.read_bytes() + b'\n')
            return real_map(*args, **kwargs)

        with mock.patch.object(self.receipt, 'frame_map',
                               side_effect=mutate_after_snapshot):
            result = self.analyze()
        self.assertTrue(altered)
        self.assertEqual(result['original']['map_sha256'], expected)
        self.assertNotEqual(hashlib.sha256(self.ref_map.read_bytes()).hexdigest(),
                            expected)

    def test_original_event_underproduction_is_rejected(self):
        # The original fixture previously passed with just seven stereo
        # samples for seven guest frames despite a 32040-Hz WAV header.
        with wave.open(str(self.wav), 'wb') as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(32040)
            w.writeframes(struct.pack('<hh', 123, -45) * 6454)
        self.ref_map.write_text('frame,samples\n' +
                                ''.join(f'{f},{f}\n' for f in range(6455)))
        with self.assertRaisesRegex(ValueError, 'original PCM coverage too short'):
            self.analyze()

    def test_native_event_underproduction_is_rejected(self):
        # The native producer can report ten complete guest frames while
        # yielding only ten stereo samples; matching lengths alone is weak.
        self.pcm.write_bytes(struct.pack('<hh', 12, -8) * 10)
        self.native_map.write_text('frame,samples\n' +
                                   ''.join(f'{f},{f - 6447}\n'
                                           for f in range(6447, 6458)))
        with self.assertRaisesRegex(ValueError, 'native PCM coverage too short'):
            self.analyze()

    def test_conservative_coverage_floor_is_inclusive(self):
        with self.assertRaisesRegex(ValueError, 'native PCM coverage too short'):
            self.receipt.require_sample_coverage(667, 10, 32040, 'native')
        self.receipt.require_sample_coverage(668, 10, 32040, 'native')

    def test_native_end_burst_cannot_hide_nine_empty_frames(self):
        # Ten completed native boundaries and 668 real PCM16 stereo samples
        # satisfy the aggregate floor, but nine consecutive frames are empty.
        self.pcm.write_bytes(struct.pack('<hh', 12, -8) * 668)
        self.native_map.write_text('frame,samples\n' +
                                   ''.join(f'{f},{0 if f < 6457 else 668}\n'
                                           for f in range(6447, 6458)))
        with self.assertRaisesRegex(
                ValueError, 'native frames 6447..6450 PCM coverage too short'):
            self.analyze()

    def test_original_end_burst_cannot_hide_six_empty_frames(self):
        # Keep the actual WAV and final map lengths unchanged. The original
        # seven-frame event has 896 samples, all falsely assigned to its last
        # boundary, while later frame counts remain consistent with the WAV.
        def sample_count(frame):
            if frame <= 6445:
                return frame
            if frame <= 6451:
                return 6445
            return 6445 + 896 + (frame - 6452) * 128

        self.ref_map.write_text('frame,samples\n' +
                                ''.join(f'{f},{sample_count(f)}\n'
                                        for f in range(6455)))
        with self.assertRaisesRegex(
                ValueError, 'original frames 6445..6448 PCM coverage too short'):
            self.analyze()

    def test_window_floor_allows_isolated_empty_frame(self):
        # A single frame can have no newly observed samples around a producer
        # boundary; neighbors still cover every 3-frame window.
        rows = {f: (f - 6447) * 128 - (128 if f >= 6450 else 0)
                for f in range(6447, 6458)}
        self.receipt.require_frame_window_coverage(
            rows, 6447, 6457, 32040, 'native')

    def test_native_two_empty_intervals_cannot_hide_in_three_frame_totals(self):
        # Each three-frame sum exceeds the weak floor, but two adjacent
        # completed guest frames have zero newly produced DSP samples.
        increments = [0, 0, 201, 0, 0, 201, 0, 0, 266, 0]
        totals = [0]
        for count in increments:
            totals.append(totals[-1] + count)
        self.pcm.write_bytes(struct.pack('<hh', 12, -8) * totals[-1])
        self.native_map.write_text('frame,samples\n' +
                                   ''.join(f'{6447 + i},{total}\n'
                                           for i, total in enumerate(totals)))
        with self.assertRaisesRegex(
                ValueError, 'native consecutive empty PCM frame intervals 6448..6449'):
            self.analyze()

    def test_original_two_empty_intervals_cannot_hide_in_three_frame_totals(self):
        # Retain the complete original WAV and map lengths, assigning the
        # seven event-frame increments to a sparse bursty callback map.
        increments = [0, 0, 300, 0, 0, 300, 296]
        totals = [0]
        for count in increments:
            totals.append(totals[-1] + count)

        def sample_count(frame):
            if frame <= 6445:
                return frame
            if frame <= 6452:
                return 6445 + totals[frame - 6445]
            return 6445 + totals[-1] + (frame - 6452) * 128

        self.ref_map.write_text('frame,samples\n' +
                                ''.join(f'{f},{sample_count(f)}\n'
                                        for f in range(6455)))
        with self.assertRaisesRegex(
                ValueError, 'original consecutive empty PCM frame intervals 6446..6447'):
            self.analyze()

    def test_native_frame_boundary_sync_timeout_rejected(self):
        self.native_log.write_text('[apu] frame-boundary guest-clock sync timed out\n')
        with self.assertRaisesRegex(ValueError, 'APU frame-boundary sync timed out'):
            self.analyze()

    def test_native_watchdog_abandoned_frame_rejected(self):
        # Pinned common_cpu_infra.c emits this marker before longjmp;
        # common_rtl.c still advances the frame counter afterward.
        self.native_log.write_text('\\n=== WATCHDOG: Frame 6450 exceeded 5.1s ===\\n')
        with self.assertRaisesRegex(ValueError, 'watchdog abandoned'):
            self.analyze()

    def test_reference_wav_truncated_tail_preserves_specific_rejection(self):
        self.wav.write_bytes(self.wav.read_bytes()[:-4])
        with self.assertRaisesRegex(ValueError, 'original WAV truncated'):
            self.analyze()

    def test_reference_wav_appended_payload_rejected(self):
        # The pinned snesref WAV writer emits exactly 44 bytes of header
        # followed by 4 bytes per callback stereo frame, with no extra chunks.
        with self.wav.open('ab') as f:
            f.write(b'UNTRUSTED-TRAILER')
        with self.assertRaisesRegex(ValueError, 'unexpected original WAV length'):
            self.analyze()


if __name__ == '__main__':
    unittest.main()
