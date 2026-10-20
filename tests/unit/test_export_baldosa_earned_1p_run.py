import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from export_baldosa_earned_1p_run import export, MAX_RUN_BYTES, SOURCE_SCOPE

class ExportEarnedRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.journey = self.base / 'journey'
        self.journey.mkdir()
        self.runs = self.journey / 'Brand New Player With Spaces' / 'runs' / 'mike'
        self.runs.mkdir(parents=True)
        self.run = self.runs / 'source.urrun'
        self.run.write_bytes(b'CI fixture only; not a real game record')
        self.report = {
            'scope': SOURCE_SCOPE,
            'second_game_loaded_named_sram_and_finished_real_source_race': True,
            'third_game_reopened_exact_earned_run_read_only': True,
            'one_canonical_run_sha256': hashlib.sha256(self.run.read_bytes()).hexdigest(),
            'release_gate_credit': 0,
            'physical_gamepad_verified': False,
            'strict_original_native_event_pass': False,
        }
        self.write_report()
        self.out = self.base / 'evidence'

    def write_report(self):
        (self.journey / 'report.json').write_text(json.dumps(self.report))

    def test_exports_exact_two_whitelisted_members_and_manifest(self):
        m = export(self.journey, self.out)
        self.assertEqual(set(p.name for p in self.out.iterdir()),
                         {'earned.urrun', 'source-report.json', 'manifest.json'})
        self.assertEqual((self.out / 'earned.urrun').read_bytes(), self.run.read_bytes())
        self.assertEqual(m['members']['earned.urrun']['sha256'], self.report['one_canonical_run_sha256'])
        self.assertFalse(m['independent_release_acceptance'])
        with self.assertRaises(FileExistsError): export(self.journey, self.out)

    def test_rejects_wrong_source_report_and_digest(self):
        for key, value in [('scope', 'synthetic'),
                           ('third_game_reopened_exact_earned_run_read_only', False),
                           ('release_gate_credit', 1),
                           ('one_canonical_run_sha256', '0'*64)]:
            with self.subTest(key=key):
                old = self.report[key]
                self.report[key] = value
                self.write_report()
                with self.assertRaises(ValueError): export(self.journey, self.out)
                self.assertFalse(self.out.exists())
                self.report[key] = old

    def test_rejects_duplicate_empty_oversized_and_symlinked_run(self):
        duplicate = self.runs / 'second.urrun'
        duplicate.write_bytes(b'extra')
        with self.assertRaises(ValueError): export(self.journey, self.out)
        duplicate.unlink()
        self.run.write_bytes(b'')
        with self.assertRaises(ValueError): export(self.journey, self.out)
        with self.run.open('wb') as stream: stream.truncate(MAX_RUN_BYTES + 1)
        with self.assertRaises(ValueError): export(self.journey, self.out)
        self.run.unlink()
        self.run.symlink_to(self.journey / 'report.json')
        with self.assertRaises(ValueError): export(self.journey, self.out)
        self.assertFalse(self.out.exists())

if __name__ == '__main__': unittest.main()
