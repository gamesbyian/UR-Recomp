"""QA01 ROM-free negative tests for same-host versus real post-return bytes.

Synthetic WRAM is used only to test a read-only *comparison* contract.
Authenticated 2014 game evidence is tested separately in the archive workflow.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf066_same_host_stack_return_raw as window
from tests.unit.test_qa01_rf066_original_consumed_sequence import actual_rows


def images():
    original = bytearray(131072)
    native = bytearray(131072)
    for offset, original_byte, native_byte in (
        (0x01ed, 0x26, 0x81), (0x01ee, 0xf0, 0x97),
        (0x01ef, 0xd4, 0x00), (0x01f0, 0x82, 0x55),
    ):
        original[offset] = original_byte
        native[offset] = native_byte
    return original, native


def pulls():
    # Both are true byte-wise aliases of one original post-return operation.
    # 01ED is original-dump matching, 01EE native-dump matching;
    # 01EF and 01F0 match neither same-host script-dump snapshot.
    return [
        {"frame": 1018, "base": 0x01ed, "width": 2,
         "returned": 0x9726, "v": 2, "h": 100},
        {"frame": 1018, "base": 0x01ef, "width": 2,
         "returned": 0x1231, "v": 2, "h": 300},
    ]


class SameFrameGuestPhases(unittest.TestCase):
    def test_post_return_values_are_not_assumed_equal_to_same_host_script_dump(self):
        a, b = images()
        r = window.row(1018, pulls(), a, b)
        self.assertEqual(r["full_original_native_wram_byte_differences"], 4)
        self.assertEqual(r["original_return_operations_touching_differing_addresses"], 2)
        self.assertEqual(r["return_byte_observations_touching_differing_addresses"], 4)
        self.assertEqual(r["individual_return_byte_values_vs_same_host_script_dump"], {
            "matches_original_same_host_dump_only": 1,
            "matches_native_same_host_dump_only": 1,
            "matches_neither_same_host_dump": 2,
        })
        self.assertEqual(r["return_byte_observation_counts_by_physical_address"], {
            "7E:01ED": 1, "7E:01EE": 1, "7E:01EF": 1, "7E:01F0": 1})
        self.assertFalse(r["same_host_frame_establishes_instruction_phase_equivalence"])

    def test_real_rf066_valid_source_macro_return_has_actual_return_value(self):
        source = window.true_returns(actual_rows(), expected_count=1)
        self.assertEqual(len(source), 1)
        self.assertEqual(source[0]["base"], 0x01ed)
        self.assertEqual(source[0]["width"], 1)
        self.assertEqual(source[0]["returned"], 0x26)

    def test_negative_provenance_and_wrong_scope_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unqualified genuine"):
            window.true_returns(actual_rows(), expected_count=903)
        for kind in ("missing_wram", "masked_interior", "no_real_returns",
                     "wrong_host_frame"):
            with self.subTest(kind=kind):
                a, b = images()
                events = pulls()
                if kind == "missing_wram":
                    a = a[:-1]
                elif kind == "masked_interior":
                    b[0x01ef] = a[0x01ef]
                elif kind == "no_real_returns":
                    events = []
                else:
                    events = [{**row, "frame": 1019} for row in events]
                with self.assertRaises(ValueError):
                    window.row(1018, events, a, b)


if __name__ == "__main__":
    unittest.main()
