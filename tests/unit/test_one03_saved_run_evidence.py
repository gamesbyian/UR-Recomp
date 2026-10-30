"""ROM-free negative controls for source-earned ONE-03 saved-run evidence."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / 'tools/verify_one03_saved_run.py'
spec = importlib.util.spec_from_file_location('verify_one03_saved_run', MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def record(*, course='course:00', ticks=1505):
    body = (f'URRUN 1\ngame uniracers-usa\nrom_sha256 {"a"*64}\n'
            f'build_compat source-pinned\ncourse {course}\nmode race-1p\n'
            f'elapsed_ticks60 {ticks}\nframe_count 2090\nterminal_digest -\n'
            f'split finish {ticks}\ninput 0 1 100 0\nEND\n').encode('ascii')
    value = 14695981039346656037
    for byte in body:
        value = ((value ^ byte) * 1099511628211) & 0xffffffffffffffff
    return body + f'checksum {value:016x}\n'.encode('ascii')


class One03SavedRunEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root = base / 'results.alpha'
        self.root.mkdir()
        self.path = self.root / 'run-123-0000.urrun'
        self.log = base / 'next-earned.log'
        self.receipt = base / 'saved.json'
        self.path.write_bytes(record())
        self.log.write_text(f'UR_RUN_RECORD CAPTURED path={self.path} course=course:00 '
                            'elapsed_ticks60=1505 origin_frame=2090 inputs=1 splits=1\n')

    def test_actual_file_checksum_and_reopen(self):
        receipt, raw = mod.verify(self.log, self.root, True)
        self.assertEqual(raw, self.path.read_bytes())
        self.assertEqual(receipt['elapsed_ticks60'], 1505)
        self.receipt.write_text(json.dumps(receipt))
        self.assertEqual(mod.verify(self.log, self.root, True, self.receipt)[0], receipt)

    def test_log_only_false_green_rejected(self):
        self.path.unlink()
        with self.assertRaisesRegex(ValueError, 'no actual saved record'):
            mod.verify(self.log, self.root, True)

    def test_corrupt_file_rejected(self):
        self.path.write_bytes(self.path.read_bytes().replace(b'1505', b'1506', 1))
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            mod.verify(self.log, self.root, True)

    def test_wrong_course_and_time_rejected(self):
        self.path.write_bytes(record(course='course:01'))
        with self.assertRaisesRegex(ValueError, 'provenance'):
            mod.verify(self.log, self.root, True)
        self.path.write_bytes(record(ticks=1506))
        with self.assertRaisesRegex(ValueError, 'provenance'):
            mod.verify(self.log, self.root, True)

    def test_replaced_after_first_receipt_rejected(self):
        receipt, _ = mod.verify(self.log, self.root, True)
        self.receipt.write_text(json.dumps(receipt))
        self.path.write_bytes(record(ticks=1506))
        with self.assertRaises(ValueError):
            mod.verify(self.log, self.root, True, self.receipt)

    def test_path_escape_and_duplicate_rejected(self):
        self.log.write_text('UR_RUN_RECORD CAPTURED path=/tmp/other.urrun course=course:00 '
                            'elapsed_ticks60=1505\n')
        with self.assertRaisesRegex(ValueError, 'escaped'):
            mod.verify(self.log, self.root, True)
        self.log.write_text((f'UR_RUN_RECORD CAPTURED path={self.path} course=course:00 '
                             'elapsed_ticks60=1505\n') * 2)
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            mod.verify(self.log, self.root, True)

    def test_symlink_record_rejected(self):
        real = self.root / 'real.urrun'
        real.write_bytes(record())
        self.path.unlink()
        try:
            self.path.symlink_to(real)
        except OSError:
            self.skipTest('symlinks unavailable')
        with self.assertRaisesRegex(ValueError, 'redirected'):
            mod.verify(self.log, self.root, True)


if __name__ == '__main__':
    unittest.main()
