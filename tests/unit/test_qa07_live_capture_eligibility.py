"""Synthetic live-video eligibility, not a production encoder/capture test."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from qa07_live_capture_eligibility import LiveCapture, State


class CaptureTests(unittest.TestCase):
    def healthy(self):
        c=LiveCapture()
        c.start(attempt='a',profile='P1',race_entry_frame=10,capture_start_frame=10)
        for i in range(10,14):
            c.frame(attempt='a',frame_number=i,composed_frame_present=True,audio_span_complete=True)
        c.finish(attempt='a',profile='P1',terminal_frame=13)
        return c

    def test_save_verified(self):
        c=self.healthy()
        self.assertEqual(c.decision('save',attempt='a',profile='P1',movie_bytes=b'mp4',verified=True),'Video saved')

    def test_discard(self):
        c=self.healthy()
        self.assertEqual(c.decision('discard',attempt='a',profile='P1'),'Video discarded')

    def test_replay_not_substitute(self):
        c=LiveCapture()
        c.start(attempt='a',profile='P1',race_entry_frame=10,capture_start_frame=11)
        with self.assertRaises(ValueError):
            c.decision('save',attempt='a',profile='P1',movie_bytes=b'replay',verified=True)

    def test_frame_gap(self):
        c=LiveCapture()
        c.start(attempt='a',profile='P1',race_entry_frame=10,capture_start_frame=10)
        c.frame(attempt='a',frame_number=11,composed_frame_present=True,audio_span_complete=True)
        self.assertEqual(c.state,State.INCOMPLETE)

    def test_missing_audio(self):
        c=LiveCapture()
        c.start(attempt='a',profile='P1',race_entry_frame=10,capture_start_frame=10)
        c.frame(attempt='a',frame_number=10,composed_frame_present=True,audio_span_complete=False)
        self.assertEqual(c.state,State.INCOMPLETE)

    def test_missing_composed_frame(self):
        c=LiveCapture()
        c.start(attempt='a',profile='P1',race_entry_frame=10,capture_start_frame=10)
        c.frame(attempt='a',frame_number=10,composed_frame_present=False,audio_span_complete=True)
        self.assertEqual(c.state,State.INCOMPLETE)

    def test_wrong_profile(self):
        c=self.healthy()
        with self.assertRaises(ValueError):
            c.decision('discard',attempt='a',profile='P2')

    def test_unverified_save(self):
        c=self.healthy()
        with self.assertRaises(ValueError):
            c.decision('save',attempt='a',profile='P1',movie_bytes=b'mp4',verified=False)
        self.assertEqual(c.state,State.READY)

    def test_wrong_attempt(self):
        c=self.healthy()
        with self.assertRaises(ValueError):
            c.decision('save',attempt='other',profile='P1',movie_bytes=b'mp4',verified=True)

    def test_terminal_missing(self):
        c=LiveCapture()
        c.start(attempt='a',profile='P1',race_entry_frame=10,capture_start_frame=10)
        c.frame(attempt='a',frame_number=10,composed_frame_present=True,audio_span_complete=True)
        c.finish(attempt='a',profile='P1',terminal_frame=11)
        self.assertEqual(c.state,State.INCOMPLETE)

    def test_repeated_start(self):
        c=LiveCapture()
        c.start(attempt='a',profile='P1',race_entry_frame=0,capture_start_frame=0)
        with self.assertRaises(ValueError):
            c.start(attempt='b',profile='P2',race_entry_frame=0,capture_start_frame=0)

    def test_zero_frame_false_success_rejected(self):
        c=LiveCapture()
        c.start(attempt='a',profile='P1',race_entry_frame=0,capture_start_frame=0)
        c.finish(attempt='a',profile='P1',terminal_frame=-1)
        self.assertEqual(c.state,State.INCOMPLETE)

    def test_invalid_identity_type(self):
        c=LiveCapture()
        with self.assertRaises(ValueError):
            c.start(attempt=True,profile='P1',race_entry_frame=0,capture_start_frame=0)

    def test_boolean_frame_rejected(self):
        c=LiveCapture()
        c.start(attempt='a',profile='P1',race_entry_frame=10,capture_start_frame=10)
        c.frame(attempt='a',frame_number=True,composed_frame_present=True,audio_span_complete=True)
        self.assertEqual(c.state,State.INCOMPLETE)


if __name__=='__main__':
    unittest.main()
