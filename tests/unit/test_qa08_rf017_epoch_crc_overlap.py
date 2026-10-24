import unittest
import tempfile
import zipfile
from pathlib import Path
from tools.qa08_rf017_epoch_crc_overlap import census, parse_old, parse_new, read_pinned_zip, sha

class EpochCrcOverlapTests(unittest.TestCase):
    def setUp(self):
        self.old = {f: f'{f:08x}' for f in range(1948,1971)}
        self.new = ['deadbeef'] * 5484

    def test_no_overlap_is_not_parity(self):
        r = census(self.old, self.new)
        self.assertEqual(r['anywhere_matching_old_values'], 0)
        self.assertFalse(r['same_semantic_stage_proven'])
        self.assertFalse(r['first_divergence_located'])
        self.assertFalse(r['release_credit'])

    def test_shifted_hash_is_detected_anywhere(self):
        self.new[100] = self.old[1948]
        r = census(self.old, self.new)
        self.assertEqual(r['anywhere_match_indices'], {'1948': [100]})
        self.assertEqual(r['same_numeric_guest_label_matches'], 0)

    def test_direct_and_adjacent_indices_are_separate(self):
        self.new[1948] = self.old[1948]
        self.new[1949] = self.old[1950]
        r = census(self.old, self.new)
        self.assertEqual(r['same_numeric_guest_label_matches'], 1)
        self.assertEqual(r['one_earlier_index_matches'], 1)

    def test_duplicate_host_trace_refused(self):
        line = 'UR_BALDOSA_HOST_FRAME_CRC host=1948 guest=1948 hash=00000001\n'
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            parse_old(line * 2)

    def test_mismatched_guest_trace_refused(self):
        with self.assertRaisesRegex(ValueError, 'labels differ'):
            parse_old('UR_BALDOSA_HOST_FRAME_CRC host=1948 guest=1949 hash=00000001')

    def test_missing_historical_window_refused(self):
        with self.assertRaisesRegex(ValueError, '23-frame'):
            parse_old('UR_BALDOSA_HOST_FRAME_CRC host=1948 guest=1948 hash=00000001')

    def test_malformed_new_crc_refused(self):
        with self.assertRaisesRegex(ValueError, 'format/count'):
            parse_new(b'0xdeadbeef\n' * 5483)

    def test_crlf_historical_trace_accepted(self):
        rows = "\r\n".join(f"UR_BALDOSA_HOST_FRAME_CRC host={f} guest={f} hash={f:08x}" for f in range(1948,1971)) + "\r\n"
        self.assertEqual(parse_old(rows), self.old)

    def test_mutated_archive_sha_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.zip"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("evidence.txt", "hello")
            with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                read_pinned_zip(p, "0" * 64, {"evidence.txt"})

    def test_duplicate_archive_member_refused(self):
        import warnings
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "duplicate.zip"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(p, "w") as z:
                    z.writestr("evidence.txt", "one")
                    z.writestr("evidence.txt", "two")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                read_pinned_zip(p, sha(p.read_bytes()), {"evidence.txt"})

    def test_complete_new_crc_accepted(self):
        self.assertEqual(len(parse_new(b'0xdeadbeef\n' * 5484)), 5484)

if __name__ == '__main__':
    unittest.main()
