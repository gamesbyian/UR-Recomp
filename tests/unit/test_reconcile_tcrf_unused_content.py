import unittest

from tools.reconcile_tcrf_unused_content import all_occurrences, lorom_file_offset, printable_runs


class TcrfReconciliationTests(unittest.TestCase):
    def test_lorom_838000_maps_to_18000(self):
        self.assertEqual(lorom_file_offset(0x838000), 0x18000)

    def test_lorom_rejects_low_half(self):
        with self.assertRaises(ValueError):
            lorom_file_offset(0x837FFF)

    def test_all_occurrences_includes_overlaps(self):
        self.assertEqual(all_occurrences(b"AAAA", b"AA"), [0, 1, 2])

    def test_printable_runs(self):
        self.assertEqual(
            printable_runs(b"\x00ABCD\xffXYZ12\x00", min_length=4),
            [
                {"relative_offset": 1, "length": 4, "text": "ABCD"},
                {"relative_offset": 6, "length": 5, "text": "XYZ12"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
