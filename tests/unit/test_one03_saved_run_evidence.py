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


def signed_body(body: bytes) -> bytes:
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
                            'elapsed_ticks60=1505 origin_frame=2090 inputs=1 splits=1 '
                            'replay_input=1 ghost_trace=0\n')

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
                            'elapsed_ticks60=1505 origin_frame=2090 inputs=1 splits=1 '
                            'replay_input=1 ghost_trace=0\n')
        with self.assertRaisesRegex(ValueError, 'escaped'):
            mod.verify(self.log, self.root, True)
        self.log.write_text((f'UR_RUN_RECORD CAPTURED path={self.path} course=course:00 '
                             'elapsed_ticks60=1505 origin_frame=2090 inputs=1 splits=1 '
                             'replay_input=1 ghost_trace=0\n') * 2)
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            mod.verify(self.log, self.root, True)

    def assert_reject_mutation(self, old: bytes, new: bytes):
        body = record().split(b'checksum ', 1)[0]
        self.assertIn(old, body)
        self.path.write_bytes(signed_body(body.replace(old, new, 1)))
        with self.assertRaises(ValueError):
            mod.verify(self.log, self.root, True)

    def test_unknown_checksum_valid_scalar_rejected(self):
        self.assert_reject_mutation(b'END\n', b'rogue foo\nEND\n')

    def test_malformed_checksum_valid_input_rejected(self):
        self.assert_reject_mutation(b'input 0 1 100 0\n', b'input nonsense\n')

    def test_malformed_checksum_valid_split_rejected(self):
        self.assert_reject_mutation(b'split finish 1505\n', b'split finish nope\n')

    def test_missing_or_duplicate_required_scalar_rejected(self):
        self.assert_reject_mutation(b'frame_count 2090\n', b'')
        self.assert_reject_mutation(b'frame_count 2090\n', b'frame_count 2090\nframe_count 2090\n')

    def test_input_native_range_and_overlap_rejected(self):
        for bad in (b'input 0 0 100 0\n', b'input 0 1 1000 0\n',
                    b'input 2090 1 100 0\n',
                    b'input 0 1 100 0\ninput 0 1 100 0\n',
                    b'input 18446744073709551616 1 100 0\n'):
            self.assert_reject_mutation(b'input 0 1 100 0\n', bad)

    def test_split_order_and_bounds_rejected(self):
        for bad in (b'split finish 1506\n', b'split finish -1\n',
                    b'split finish 1505\nsplit later 1499\n',
                    b'split finish 18446744073709551616\n'):
            self.assert_reject_mutation(b'split finish 1505\n', bad)

    def test_invalid_native_tokens_and_u64_rejected(self):
        self.assert_reject_mutation(b'build_compat source-pinned\n',
                                    b'build_compat not/allowed\n')
        self.assert_reject_mutation(b'frame_count 2090\n',
                                    b'frame_count 18446744073709551616\n')
        self.assert_reject_mutation(b'terminal_digest -\n',
                                    b'terminal_digest not-a-hash\n')

    def test_non_lf_ascii_separators_rejected(self):
        # Python splitlines() treats these as row separators; C++ std::getline
        # only splits on LF, so none may create a second valid native row.
        original = b'frame_count 2090\nterminal_digest -\n'
        for separator in (b'\x0b', b'\x0c', b'\x1c', b'\x1d', b'\x1e', b'\r'):
            body = record().split(b'checksum ', 1)[0]
            self.assertIn(original, body)
            body = body.replace(original,
                                b'frame_count 2090' + separator + b'terminal_digest -\n', 1)
            self.path.write_bytes(signed_body(body))
            with self.subTest(separator=separator), self.assertRaises(ValueError):
                mod.verify(self.log, self.root, True)

    def test_producer_counts_and_finish_split_match_saved_bytes(self):
        self.assert_reject_mutation(b'input 0 1 100 0\n', b'')
        self.assert_reject_mutation(b'split finish 1505\n', b'')
        self.assert_reject_mutation(b'split finish 1505\n', b'split finish 1504\n')
        # Negative controls deliberately leave the fixture corrupted; restore
        # the valid saved bytes before testing log-only count tampering.
        self.path.write_bytes(record())
        original = self.log.read_text()
        for altered in (original.replace('inputs=1', 'inputs=2'),
                        original.replace('splits=1', 'splits=2'),
                        original.replace('inputs=1', 'inputs=18446744073709551616')):
            self.log.write_text(altered)
            with self.assertRaises(ValueError):
                mod.verify(self.log, self.root, True)
        self.log.write_text(original)
        self.assertEqual(mod.verify(self.log, self.root, True)[0]['elapsed_ticks60'], 1505)

    def test_native_valid_multiple_splits_and_inputs(self):
        body = record().split(b'checksum ', 1)[0]
        body = body.replace(b'split finish 1505\n', b'split early 500\nsplit finish 1505\n')
        body = body.replace(b'input 0 1 100 0\n',
                            b'input 0 1 100 0\ninput 10 2 0 A00\n')
        self.path.write_bytes(signed_body(body))
        self.log.write_text(self.log.read_text().replace('inputs=1 splits=1',
                                                         'inputs=2 splits=2'))
        receipt, raw = mod.verify(self.log, self.root, True)
        self.assertEqual(receipt['sha256'], __import__('hashlib').sha256(raw).hexdigest())

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
