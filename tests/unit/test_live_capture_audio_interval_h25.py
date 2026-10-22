"""Recovered H25 48-kHz/PTS checks adapted to the current capture witness.

All data are synthetic. No independent device, encoded movie or release claim.
"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools' / 'live_capture_research'))
from clock_bound_audio_span import ClockBoundWitness
from live_audio_span_witness import ByteSpanWitness


class H25AudioIntervalTests(unittest.TestCase):
    def witness(self, cls=ClockBoundWitness):
        return cls(attempt='race', profile='p', width=1, height=1, entry_frame=0)

    def add(self, w, n, pts_ns, first, samples):
        w.add(attempt='race', frame_number=n, pts_ns=pts_ns,
              bgra=b'\x01\x02\x03\xff', audio_first_sample=first,
              pcm_s16le=b'\x00\x00\x00\x00' * samples)

    def test_preexisting_byte_span_allows_audio_far_short_of_video(self):
        w = self.witness(ByteSpanWitness)
        self.add(w, 0, 0, 0, 1)
        self.add(w, 1, 16_666_667, 1, 1)
        self.assertEqual(w.finish(attempt='race', profile='p', terminal_frame=1)
                         ['audio_samples_48k_stereo'], 2)
        hardened = self.witness()
        self.add(hardened, 0, 0, 0, 1)
        with self.assertRaisesRegex(ValueError, 'audio span does not match'):
            self.add(hardened, 1, 16_666_667, 1, 1)

    def test_original_two_frame_60hz_positive_and_sealed_receipt(self):
        w = self.witness()
        self.add(w, 0, 0, 0, 800)
        self.add(w, 1, 16_666_667, 800, 800)
        receipt = w.finish(attempt='race', profile='p', terminal_frame=1,
                           terminal_pts_ns=33_333_334)
        self.assertEqual(receipt['audio_samples_48k_stereo'], 1600)
        self.assertEqual(receipt['terminal_pts_ns'], 33_333_334)
        self.assertTrue(receipt['clock_checked_against_48k_samples'])
        self.assertFalse(receipt['encoded_video_verified'])
        self.assertFalse(receipt['independent_device_clock_observed'])
        self.assertEqual(receipt['release_gate_credit'], 0)
        with self.assertRaisesRegex(ValueError, 'finalized'):
            w.finish(attempt='race', profile='p', terminal_frame=1,
                     terminal_pts_ns=33_333_334)
        with self.assertRaisesRegex(ValueError, 'finalized'):
            self.add(w, 2, 33_333_334, 1600, 800)

    def test_short_terminal_audio_or_one_frame_refuses(self):
        w = self.witness()
        self.add(w, 0, 0, 0, 800)
        with self.assertRaisesRegex(ValueError, 'insufficient'):
            w.finish(attempt='race', profile='p', terminal_frame=0,
                     terminal_pts_ns=16_666_667)
        self.add(w, 1, 16_666_667, 800, 1)
        with self.assertRaisesRegex(ValueError, 'terminal audio span'):
            w.finish(attempt='race', profile='p', terminal_frame=1,
                     terminal_pts_ns=33_333_334)

    def test_invalid_or_backwards_terminal_time_refuses(self):
        for invalid in (None, True, 16_666_667, 0, '33333334'):
            with self.subTest(value=invalid):
                w = self.witness()
                self.add(w, 0, 0, 0, 800)
                self.add(w, 1, 16_666_667, 800, 800)
                with self.assertRaises(ValueError):
                    w.finish(attempt='race', profile='p', terminal_frame=1,
                             terminal_pts_ns=invalid)

    def test_wrong_audio_cursor_and_missing_frame_remain_refused(self):
        w = self.witness()
        self.add(w, 0, 0, 0, 800)
        with self.assertRaisesRegex(ValueError, 'audio gap/overlap'):
            self.add(w, 1, 16_666_667, 799, 800)
        w = self.witness()
        self.add(w, 0, 0, 0, 800)
        with self.assertRaisesRegex(ValueError, 'frame/attempt discontinuity'):
            self.add(w, 2, 16_666_667, 800, 800)

    def test_one_sample_rounding_tolerance_but_not_two(self):
        for first_samples in (799, 800, 801):
            with self.subTest(first_samples=first_samples):
                w = self.witness()
                self.add(w, 0, 0, 0, first_samples)
                self.add(w, 1, 16_666_667, first_samples, 800)
                self.assertTrue(w.finish(attempt='race', profile='p', terminal_frame=1,
                                         terminal_pts_ns=33_333_334)
                                ['clock_checked_against_48k_samples'])
        w = self.witness()
        self.add(w, 0, 0, 0, 798)
        with self.assertRaisesRegex(ValueError, 'audio span does not match'):
            self.add(w, 1, 16_666_667, 798, 800)

    def test_failed_finish_cannot_claim_receipt_or_late_mutation(self):
        w = self.witness()
        self.add(w, 0, 0, 0, 800)
        self.add(w, 1, 16_666_667, 800, 800)
        with self.assertRaisesRegex(ValueError, 'no complete attempt-bound'):
            w.finish(attempt='race', profile='wrong', terminal_frame=1,
                     terminal_pts_ns=33_333_334)
        # Valid caller can retry a denied identity; the data were not modified.
        self.assertEqual(w.finish(attempt='race', profile='p', terminal_frame=1,
                                  terminal_pts_ns=33_333_334)['frames'], 2)


if __name__ == '__main__':
    unittest.main()
