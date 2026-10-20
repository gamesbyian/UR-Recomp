import hashlib
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
import sys
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from export_baldosa_earned_1p_run import export, MAX_RUN_BYTES, SOURCE_SCOPE

class ExportEarnedRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.journey = self.base / 'journey with spaces'
        self.journey.mkdir()
        self.runs = self.journey / 'Brand New Player With Spaces' / 'runs' / 'mike'
        self.runs.mkdir(parents=True)
        self.run = self.runs / 'source.urrun'
        self.run.write_bytes(b'CI fixture only; not a real game record')
        self.report = {
            'scope': SOURCE_SCOPE,
            'first_game_created_first_named_racer': True,
            'second_game_loaded_named_sram_and_finished_real_source_race': True,
            'active_selector_and_catalog_preserved': True,
            'anonymous_sram_preserved': True,
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
                           ('first_game_created_first_named_racer', False),
                           ('active_selector_and_catalog_preserved', False),
                           ('anonymous_sram_preserved', False),
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

    def test_cli_handles_space_bearing_journey_and_publishes_only_complete(self):
        script = Path(__file__).resolve().parents[2] / 'tools' / 'export_baldosa_earned_1p_run.py'
        destination = self.journey / 'ci owned earned 1p run'
        completed = subprocess.run(
            [sys.executable, str(script), '--journey', str(self.journey),
             '--out', str(destination)], text=True, capture_output=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(self.report['one_canonical_run_sha256'], completed.stdout)
        self.assertEqual(set(p.name for p in destination.iterdir()),
                         {'earned.urrun', 'source-report.json', 'manifest.json'})
        self.assertEqual((destination / 'earned.urrun').read_bytes(), self.run.read_bytes())

    def test_failed_export_never_publishes_partial_artifact(self):
        import export_baldosa_earned_1p_run as module
        original = module._regular_bytes
        def fail_after_copy(path, limit):
            if path.name == 'earned.urrun':
                raise OSError('injected evidence readback failure')
            return original(path, limit)
        with patch.object(module, '_regular_bytes', side_effect=fail_after_copy):
            with self.assertRaises(OSError):
                export(self.journey, self.out)
        self.assertFalse(self.out.exists())
        self.assertFalse(list(self.journey.glob('.pending-earned-1p-*')))

    def test_rejects_boolean_release_credit(self):
        self.report['release_gate_credit'] = False
        self.write_report()
        with self.assertRaises(ValueError):
            export(self.journey, self.out)
        self.assertFalse(self.out.exists())

    def test_cli_rejects_symlinked_journey(self):
        import subprocess
        script = Path(__file__).resolve().parents[2] / 'tools' / 'export_baldosa_earned_1p_run.py'
        link = self.base / 'linked journey'
        link.symlink_to(self.journey, target_is_directory=True)
        run = subprocess.run([sys.executable, str(script), '--journey', str(link),
                              '--out', str(self.out)], capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse(self.out.exists())

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
