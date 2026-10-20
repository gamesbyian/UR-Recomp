"""RF062 source-script delta classifications are not emulator noninterference."""
import hashlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf062_script_only_provenance as case


BASE=b"wait 3\ndump scene-05100\nwait 20\ndump scene-05120\n"
RAW=(b"wait 3\ndump scene-05100\n"
     b"wait 5\ndump qa01-frame-005105\n"
     b"wait 1\ndump qa01-frame-005106\n"
     b"wait 1\ndump qa01-frame-005107\n"
     b"wait 13\ndump scene-05120\n")


class ScriptProvenanceNotInstructionEquivalence(unittest.TestCase):
    def verify(self,before=BASE,after=RAW):
        with patch.object(case,"BASE_SCRIPT_SHA",hashlib.sha256(before).hexdigest()),\
             patch.object(case,"RAW_SCRIPT_SHA",hashlib.sha256(after).hexdigest()):
            return case.comparable_script(before,after)

    def test_only_three_added_dumps_partition_original_wait(self):
        r=self.verify()
        self.assertTrue(r["normalized_original_control_command_sequence_equal"])
        self.assertTrue(r["unchanged_20_frame_wait_total_around_added_dump_commands"])
        self.assertEqual(r["added_dumps_at_exact_declared_script_relative_frames"],
                         [5105,5106,5107])
        self.assertFalse(r["actual_guest_acknowledgment_clocks_independently_reopened"])
        self.assertFalse(r["extra_script_commands_are_CPU_invisible_proven"])
        self.assertEqual(r["raw_additional_script_dump_commands"],
                         list(case.REQUIRED_EXTRA_DUMPS))

    def test_broken_dump_scope_or_reordering_fails_closed(self):
        for edit in (
            RAW.replace(b"005106",b"005166"),
            RAW.replace(b"005106",b"005107",1),
            RAW.replace(b"wait 13",b"wait 14"),
            RAW.replace(b"wait 5\ndump qa01-frame-005105",
                        b"wait 4\ndump qa01-frame-005105").replace(
                        b"wait 1\ndump qa01-frame-005106",
                        b"wait 2\ndump qa01-frame-005106"),

            RAW.replace(b"scene-05120",b"scene-05121"),
            RAW.replace(b"wait 1\ndump qa01-frame-005106",b"wait 1\npress a 1\ndump qa01-frame-005106"),
        ):
            with self.subTest(edit=edit),self.assertRaises(ValueError):
                self.verify(after=edit)

    def test_noncanonical_script_refused(self):
        with self.assertRaises(ValueError):
            case.source_commands(b"wait 3\r\n")
        with self.assertRaises(ValueError):
            case.source_commands(b"wait 3")
        with self.assertRaises(ValueError):
            case.source_commands(b"wait 3\n\n")

if __name__=="__main__":
    unittest.main()
