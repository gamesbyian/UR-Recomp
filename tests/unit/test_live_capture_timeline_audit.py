"""ROM-free negative controls for declared live capture source clock metadata."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / 'tools/live_capture_timeline_audit.py'
spec = importlib.util.spec_from_file_location('live_capture_timeline_audit', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fixture():
    return {
        'attempt': 'attempt-A', 'profile': 'profile-P',
        'entry_pts_ns': 1_000_000_000, 'exit_pts_ns': 1_033_333_333,
        'first_frame': 41, 'first_source_present_id': 170,
        'audio_device_entry_cursor': 4000, 'audio_device_exit_cursor': 5600,
        'frames': [
            {'attempt': 'attempt-A', 'profile': 'profile-P', 'frame': 41,
             'source_present_id': 170, 'captured_pts_ns': 1_000_000_000,
             'source_pts_ns': 1_000_000_000, 'audio_first_sample': 0,
             'audio_samples': 800},
            {'attempt': 'attempt-A', 'profile': 'profile-P', 'frame': 42,
             'source_present_id': 171, 'captured_pts_ns': 1_016_666_667,
             'source_pts_ns': 1_016_666_667, 'audio_first_sample': 800,
             'audio_samples': 800},
        ]}


def fixture_120hz():
    """Two host presentations per 60-Hz guest tick, with 48-kHz audio."""
    f = fixture()
    f['frames'] = []
    for i, guest_frame in enumerate((41, 41, 42, 42)):
        pts = f['entry_pts_ns'] + round(i * 1_000_000_000 / 120)
        f['frames'].append({
            'attempt': f['attempt'], 'profile': f['profile'],
            'frame': guest_frame, 'source_present_id': 170 + i,
            'captured_pts_ns': pts, 'source_pts_ns': pts,
            'audio_first_sample': 400 * i, 'audio_samples': 400,
        })
    return f


class CaptureTimelineAudit(unittest.TestCase):
    def test_valid_declared_metadata_never_qualifies_movie(self):
        result = mod.audit_timeline(fixture())
        self.assertTrue(result['source_timeline_consistent'])
        self.assertFalse(result['encoded_video_verified'])
        self.assertFalse(result['independent_observation_authenticated'])
        self.assertFalse(result['release_gate_credit'])

    def test_120hz_repeated_guest_frame_is_valid_declaration_only(self):
        result = mod.audit_timeline(fixture_120hz())
        self.assertEqual(result['frames'], 4)
        self.assertFalse(result['independent_observation_authenticated'])
        self.assertFalse(result['encoded_video_verified'])
        self.assertFalse(result['release_gate_credit'])

    def test_120hz_real_guest_gap_still_rejected(self):
        f = fixture_120hz()
        f['frames'][2]['frame'] = 43
        f['frames'][3]['frame'] = 43
        with self.assertRaisesRegex(mod.TimelineError, 'guest frame'):
            mod.audit_timeline(f)

    def test_120hz_guest_regression_still_rejected(self):
        f = fixture_120hz()
        f['frames'][2]['frame'] = 40
        with self.assertRaisesRegex(mod.TimelineError, 'guest frame'):
            mod.audit_timeline(f)

    def test_120hz_source_present_gap_still_rejected(self):
        f = fixture_120hz()
        f['frames'][2]['source_present_id'] = 173
        with self.assertRaisesRegex(mod.TimelineError, 'source presentation'):
            mod.audit_timeline(f)

    def test_frame_gap(self):
        f = fixture(); f['frames'][1]['frame'] = 43
        with self.assertRaisesRegex(mod.TimelineError, 'guest frame'):
            mod.audit_timeline(f)

    def test_source_present_gap(self):
        f = fixture(); f['frames'][1]['source_present_id'] = 173
        with self.assertRaisesRegex(mod.TimelineError, 'source presentation'):
            mod.audit_timeline(f)

    def test_clock_forgery(self):
        f = fixture(); f['frames'][1]['source_pts_ns'] += 1
        with self.assertRaisesRegex(mod.TimelineError, 'clock mismatch'):
            mod.audit_timeline(f)

    def test_audio_gap(self):
        f = fixture(); f['frames'][1]['audio_first_sample'] += 1
        with self.assertRaisesRegex(mod.TimelineError, 'audio sample gap'):
            mod.audit_timeline(f)

    def test_missing_entry(self):
        f = fixture(); f['entry_pts_ns'] -= 1_000_000_000
        with self.assertRaisesRegex(mod.TimelineError, 'race entry'):
            mod.audit_timeline(f)

    def test_tail_overrun(self):
        f = fixture(); f['audio_device_exit_cursor'] += 96000
        with self.assertRaisesRegex(mod.TimelineError, 'device cursor'):
            mod.audit_timeline(f)

    def test_cross_profile(self):
        f = fixture(); f['frames'][1]['profile'] = 'other'
        with self.assertRaisesRegex(mod.TimelineError, 'cross-attempt'):
            mod.audit_timeline(f)

    def test_noninteger_boolean_rejected(self):
        f = fixture(); f['frames'][1]['audio_samples'] = True
        with self.assertRaisesRegex(mod.TimelineError, 'invalid audio'):
            mod.audit_timeline(f)

    def test_frame_audio_clock_drift(self):
        f = fixture()
        f['frames'][1]['captured_pts_ns'] += 8_000_000
        f['frames'][1]['source_pts_ns'] += 8_000_000
        with self.assertRaisesRegex(mod.TimelineError, 'clock drift'):
            mod.audit_timeline(f)

    def test_exit_clock_mismatch(self):
        f = fixture(); f['exit_pts_ns'] += 1_000_000_000
        with self.assertRaisesRegex(mod.TimelineError, 'audio tail'):
            mod.audit_timeline(f)

    def test_duplicate_json_key_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'bad.json'; p.write_text('{"attempt":"a","attempt":"b"}')
            proc = subprocess.run([sys.executable, str(SCRIPT), str(p)],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertIn('duplicate JSON key', proc.stdout)


if __name__ == '__main__':
    unittest.main()
