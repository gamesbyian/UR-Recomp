"""RF048: source/native first-consumer report refuses missing/tampered witness."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tools"))
import qa01_rf048_original_sound_pointer_report as rf

SOURCE_ROW = (
    "QA01RF048ORIGPTR count=1 frame=6073 v=196 h=902 "
    "dp_base=0000 dp_slot=0063 mirror=1 raw_ptr=13C774 y=0000 "
    "effective_candidate=13C774 a0=0080 a1=0024 target=1"
)

def native_records():
    return "\n".join([
      "QA01RF037NATIVEPTR frame=6056 bank=00 addr=0063 width=2 val=C773 A=00BD scope=Snd_IncDataPtr_M1X0",
      "QA01RF037NATIVEPTR frame=6057 bank=00 addr=0063 width=2 val=C774 A=00BD scope=Snd_UploadBlock_80D1_M1X0",
      "QA01RF037NATIVEPTR frame=6061 bank=00 addr=0063 width=2 val=D0B3 A=00FD scope=Snd_IncDataPtr_M1X0",
      "QA01RF037NATIVEPTR frame=6062 bank=00 addr=0063 width=2 val=D0B4 A=00FD scope=Snd_UploadBlock_80D1_M1X0",
    ])

class FirstConsumerReportTest(unittest.TestCase):
    def test_source_and_native_positive_no_false_cross_epoch(self):
        out=rf.classify(SOURCE_ROW,native_records())
        self.assertEqual(out["original_target_raw_pointer_rows"],1)
        self.assertEqual(out["original_exact_13C774_source_operand_observations"],1)
        self.assertEqual(out["original_indexed_candidate_by_bank"],{"13":1})
        self.assertEqual(out["native_verified_boundary_read_pairs"][0]["native_first_bus_helper_read"],"C774")
        self.assertEqual(out["native_verified_boundary_read_pairs"][1]["native_first_bus_helper_read"],"D0B4")
        self.assertFalse(out["source_original_internal_frame_equals_native_host_proven"])
        self.assertFalse(out["original_effective_pointer_vs_native_consumer_proven"])
        self.assertEqual(out["complete_USA_event_credit"],0)

    def test_no_original_matching_target_is_coverage_not_parity(self):
        # Source clears its DP base and advances Y, so an indexed match
        # must be reported even when the raw pointer is not in that range.
        out=rf.classify(SOURCE_ROW.replace("target=1","target=0"),native_records())
        self.assertEqual(out["source_window_coverage"],"indexed_candidate_observed")
        self.assertEqual(out["original_indexed_effective_candidate_rows"],1)
        absent=rf.classify(SOURCE_ROW.replace("target=1","target=0")
                          .replace("effective_candidate=13C774",
                                   "effective_candidate=13B100"),native_records())
        self.assertEqual(absent["source_window_coverage"],"sparse_source_samples_no_indexed_target")
        self.assertFalse(out["original_native_SPC_publication_causality_proven"])

    def test_missing_bad_duplicate_truncated_and_reordered_rejected(self):
        with self.assertRaisesRegex(ValueError,"did not execute"):
            rf.classify("",native_records())
        with self.assertRaisesRegex(ValueError,"truncated original"):
            rf.classify(SOURCE_ROW+"\nQA01RF048ORIGPTR_TRUNCATED",native_records())
        with self.assertRaisesRegex(ValueError,"missing real native"):
            rf.classify(SOURCE_ROW,native_records().replace("frame=6062","frame=6063"))
        with self.assertRaisesRegex(ValueError,"pointer-consumer boundary differs"):
            rf.classify(SOURCE_ROW,native_records().replace("val=C774","val=C775"))
        with self.assertRaisesRegex(ValueError,"regress/duplicate"):
            rf.classify(SOURCE_ROW+"\n"+SOURCE_ROW,native_records())
        with self.assertRaisesRegex(ValueError,"cannot be outside WRAM mirror"):
            rf.classify(SOURCE_ROW.replace("mirror=1","mirror=0"),native_records())
        with self.assertRaisesRegex(ValueError,"incomplete original"):
            rf.classify(SOURCE_ROW.replace(" y=0000",""),native_records())
        self.assertEqual(
            rf.classify(SOURCE_ROW+" indexed_target=1",native_records())
              ["original_indexed_effective_candidate_rows"],1)
        with self.assertRaisesRegex(ValueError,"indexed target disagrees"):
            rf.classify(SOURCE_ROW+" indexed_target=0",native_records())

if __name__=="__main__":
    unittest.main()
