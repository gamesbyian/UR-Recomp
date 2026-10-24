"""ROM-free staging race regression for the source-earned Windows run exporter.

Recovered from Evidence Library archive 142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ
(h26.zip -> evidence/agent3-h25.zip -> integration_tests/, 3,036 bytes, full
SHA-256 verified on a runner). Mutates the source mid-copy via the readback
hook; complements the json.dump-time mutation tests in
test_export_baldosa_earned_1p_run.py.

A source mutation during the staging copy must not publish a misleading
immutable artifact. Does not prove adversarial NTFS reparse or power-loss safety.
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import export_baldosa_earned_1p_run as exporter


class SourceStagingMutation(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.journey = self.root / 'journey'
        self.runs = self.journey / 'Brand New Player With Spaces' / 'runs' / 'mike'
        self.runs.mkdir(parents=True)
        self.run = self.runs / 'source.urrun'
        self.run.write_bytes(b'synthetic-run-only')
        report = {
            'scope': exporter.SOURCE_SCOPE,
            'first_game_created_first_named_racer': True,
            'second_game_loaded_named_sram_and_finished_real_source_race': True,
            'third_game_reopened_exact_earned_run_read_only': True,
            'active_selector_and_catalog_preserved': True,
            'anonymous_sram_preserved': True,
            'physical_gamepad_verified': False,
            'strict_original_native_event_pass': False,
            'release_gate_credit': 0,
            'one_canonical_run_sha256': hashlib.sha256(self.run.read_bytes()).hexdigest(),
        }
        (self.journey / 'report.json').write_text(json.dumps(report))

    def mutate_during_staging(self, mutation):
        original = exporter._regular_bytes
        fired = []
        def read(path, limit):
            payload = original(path, limit)
            if path.name == 'earned.urrun' and not fired:
                fired.append(True)
                mutation()
            return payload
        with patch.object(exporter, '_regular_bytes', side_effect=read):
            with self.assertRaisesRegex(ValueError, 'changed during staging'):
                exporter.export(self.journey, self.root / 'published')
        self.assertTrue(fired)
        self.assertFalse((self.root / 'published').exists())

    def test_run_rewritten_during_staging(self):
        self.mutate_during_staging(lambda: self.run.write_bytes(b'replaced-run'))

    def test_report_rewritten_during_staging(self):
        self.mutate_during_staging(lambda: (self.journey / 'report.json').write_text('{}'))

    def test_new_windows_visible_run_during_staging(self):
        self.mutate_during_staging(lambda: (self.runs / 'other.URRUN').write_bytes(b'second'))

    def test_unchanged_source_still_publishes(self):
        receipt = exporter.export(self.journey, self.root / 'published')
        self.assertEqual(receipt['source_run_filename'], 'source.urrun')
        self.assertTrue((self.root / 'published' / 'manifest.json').is_file())


if __name__ == '__main__':
    unittest.main()
