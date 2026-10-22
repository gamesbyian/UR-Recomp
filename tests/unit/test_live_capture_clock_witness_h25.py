"""First-party H25 ROM-free independent presentation-clock witness tests."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools' / 'live_capture_research'))
from presented_source_clock_admission import SourceClockPresentedWitness


class IndependentSourceClockTests(unittest.TestCase):
    def make(self):
        return SourceClockPresentedWitness(attempt='a', profile='p', width=1, height=1, entry_frame=0)

    def add(self, w, **overrides):
        args = dict(independent_source_pts_ns=1_000_000_000,
                    independent_source_present_clock=True, presented_frame_id=7,
                    independent_present_observation=True, source_attempt='a',
                    source_profile='p', attempt='a', frame_number=0,
                    pts_ns=1_000_000_000, bgra=b'\0' * 4,
                    audio_first_sample=0, pcm_s16le=b'\0' * 4)
        args.update(overrides)
        w.add_clock_bound_source_frame(**args)

    def finish_args(self):
        return dict(terminal_presented_frame_id=7, independent_terminal_presented_id=True,
                    entry_presented_frame_id=7, independent_entry_presented_id=True,
                    entry_event_pts_ns=1_000_000_000, independent_entry_event=True,
                    entry_attempt='a', entry_profile='p', terminal_event_pts_ns=1_000_020_833,
                    independent_terminal_event=True, device_entry_cursor=0, device_end_cursor=1,
                    independent_device_observation=True, attempt='a', profile='p',
                    terminal_frame=0, exit_attempt='a', exit_profile='p',
                    exit_frame=0, independent_exit_identity=True)

    def test_independent_clock_full_census_never_claims_video(self):
        witness = self.make()
        self.add(witness)
        result = witness.finish_clock_bound(**self.finish_args())
        self.assertTrue(result['independent_source_clock_census_matched'])
        self.assertTrue(result['independent_presented_frame_census_matched'])
        self.assertTrue(result['independent_race_exit_identity_matched'])
        self.assertFalse(result['encoded_video_verified'])

    def test_capture_pts_which_disagrees_with_source_is_rejected(self):
        witness = self.make()
        with self.assertRaisesRegex(ValueError, 'source presentation clock mismatch'):
            self.add(witness, independent_source_pts_ns=1_000_000_123)

    def test_missing_independent_present_flag_rejected(self):
        witness = self.make()
        with self.assertRaisesRegex(ValueError, 'source presentation clock mismatch'):
            self.add(witness, independent_source_present_clock=False)

    def test_wrong_race_identity_rejected(self):
        witness = self.make()
        with self.assertRaisesRegex(ValueError, 'unqualified source-presented frame identity'):
            self.add(witness, source_profile='not-p')

    def test_frame_submitted_without_independent_clock_never_passes_finish(self):
        witness = self.make()
        witness.add_source_frame(presented_frame_id=7, independent_present_observation=True,
                                 source_attempt='a', source_profile='p', attempt='a',
                                 frame_number=0, pts_ns=1_000_000_000, bgra=b'\0' * 4,
                                 audio_first_sample=0, pcm_s16le=b'\0' * 4)
        with self.assertRaisesRegex(ValueError, 'not all captured frames'):
            witness.finish_clock_bound(**self.finish_args())

    def test_wrong_device_audio_cursor_never_passes_terminal(self):
        witness = self.make()
        self.add(witness)
        args = self.finish_args()
        args['device_end_cursor'] = 2
        with self.assertRaisesRegex(ValueError, 'independent audio device cursor mismatch'):
            witness.finish_clock_bound(**args)


if __name__ == '__main__':
    unittest.main()
