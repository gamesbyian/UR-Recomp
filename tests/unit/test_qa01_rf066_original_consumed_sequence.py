"""RF066 proof obligations: actually returned source stack bytes, never fake reads."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf045_source_stack_macro_witness as rf45
import qa01_rf064_original_post_call_pull as rf64
import qa01_rf066_original_consumed_sequence as witness
import qa01_rf066_original_consumed_report as receipt


def staged_operations():
    old=('#include "cpumacro.h"\n'+rf45.HELPER+'\n'
         +rf45.PULL_B_NEW+'\n'+rf45.PULL_NEW)
    return rf64.patch(old)


def actual_rows():
    return (
      "QA01RF063ORIGBUS seq=1 f=1017 v=225 h=56 kind=wb"
      " bank=00 addr=01ED width=1 sampled=0026"
      " pc=80:B0E8 S=01ED phase=getset_entry\n"
      "QA01RF063ORIGCHECKPOINT seq=2 f=1017 f1=1017"
      " phase=post_real_nmi_push stack=26F0D48226"
      " v=225 h=65 pc=80:B0EB\n"
      "QA01RF044ORIGNMI f=1017 f1=1017 pc=82D4F0 S0=01F0 S1=01ED"
      " old=8197005526 new=26F0D48226\n"
      "QA01RF066ORIGCONSUMED seq=3 f=1018 v=225 h=80"
      " phase=post_real_stack_getter_return kind=pullB base=01ED"
      " width=1 returned=0026 before=2 after=2 bounded=1"
      " postPB=80 postPC=B0EB\n"
      "QA01RF045ORIGSTACK seq=1 f=1018 v=225 h=80 kind=pullB"
      " addr=01ED width=1 value=0026 sp0=01EC sp1=01ED pc=80:B0EB\n"
      "QA01RF064ORIGPULL f=1018 v=225 h=80 kind=pullB base=01ED"
      " width=1 returned=0026 before=2 after=2 unique=0 pc=80:B0EB\n"
    )


class SourceInstrument(unittest.TestCase):
    def test_actual_source_macro_one_return_no_guest_operations(self):
        original=staged_operations()
        modified=witness.patch(original)
        self.assertIn(witness.STAMP,modified)
        self.assertEqual(modified.count('QA01RF066ORIGCONSUMED seq='),1)
        self.assertEqual(modified.count('++ur_rf063_source_bus_seq'),1)
        for op in ("S9xGetByte(", "S9xGetWord(", "S9xSetByte(",
                   "S9xSetWord(", "S9xOpcode_NMI();"):
            self.assertEqual(original.count(op),modified.count(op))
        self.assertIn('phase=post_real_stack_getter_return',modified)
        self.assertEqual(modified.count('ur_rf045_stack_note("pullB"'),1)
        self.assertEqual(modified.count('ur_rf064_post_pull("pullW"'),1)

    def test_partial_or_double_staging_rejected(self):
        old=staged_operations()
        with self.assertRaisesRegex(ValueError,"requires unmodified"):
            witness.patch(old.replace(rf64.STAMP,"UNKNOWN"))
        with self.assertRaisesRegex(ValueError,"already"):
            witness.patch(witness.patch(old))
        with self.assertRaisesRegex(ValueError,"requires unmodified"):
            witness.patch(old.replace('One eligible RF063 getset entry',"Zero eligible RF063 getset entry"))


class SourceEvidence(unittest.TestCase):
    def test_true_return_sequenced_without_fabricating_getset_read(self):
        r=receipt.examine(actual_rows())
        self.assertEqual(r["total_sequenced_original_source_events"],3)
        self.assertEqual(r["sequenced_source_getset_entries"],1)
        self.assertEqual(r["sequenced_source_getset_read_entries"],0)
        self.assertEqual(r["real_source_original_post_NMI_raw_5_stack_bytes"],"26F0D48226")
        self.assertEqual(r["actual_original_post_getter_return_count"],1)
        self.assertEqual(r["actual_original_returns_with_no_other_RF063_event_inside_getter"],1)
        self.assertTrue(r["real_original_return_matches_RF045_and_RF064"])
        self.assertTrue(r["all_original_returns_strictly_positional_across_RF045_RF064_RF066"])
        self.assertTrue(r["strict_source_clock_domain_original_only"])
        self.assertFalse(r["getset_entry_time_return_value_proven"])
        self.assertFalse(r["eligible_for_qa01_causal_window"])
        self.assertEqual(r["accepted_USA_events"],0)

    def test_actual_original_interleaving_flag_retains_uncertainty(self):
        b=actual_rows()
        b=b.replace("before=2 after=2 bounded=1","before=1 after=2 bounded=0")
        b=b.replace("before=2 after=2 unique=0","before=1 after=2 unique=0")
        r=receipt.examine(b)
        self.assertEqual(r["actual_original_returns_with_intervening_RF063_events"],1)
        self.assertFalse(r["eligible_for_qa01_causal_window"])

    def test_rejects_genuine_value_assigned_to_wrong_source_clock_or_pc(self):
        # These forged rows preserve every value/frame/memory multiset.
        # Before positional qualification, the producer's Counter checks
        # accepted the wrong host H-clock or original post-call PB:PCw.
        variants = (
            actual_rows().replace("QA01RF066ORIGCONSUMED seq=3 f=1018 v=225 h=80",
                                  "QA01RF066ORIGCONSUMED seq=3 f=1018 v=225 h=81"),
            actual_rows().replace("postPB=80 postPC=B0EB",
                                  "postPB=81 postPC=B0EB"),
            actual_rows().replace("QA01RF045ORIGSTACK seq=1 f=1018 v=225 h=80",
                                  "QA01RF045ORIGSTACK seq=1 f=1018 v=225 h=79"),
        )
        for index, corrupted in enumerate(variants):
            with self.subTest(index=index), self.assertRaisesRegex(
                    ValueError, "source clock or operation order|PB:PCw context"):
                receipt.examine(corrupted)

    def test_rejects_missing_normalized_or_counterfeit_return(self):
        good=actual_rows()
        trials=(
          good.replace("seq=3 f=1018","seq=4 f=1018"),
          good.replace("seq=3 f=1018","seq=2 f=1018"),
          good.replace("before=2 after=2 bounded=1","before=1 after=2 bounded=1"),
          good.replace("before=2 after=2 bounded=1","before=2 after=3 bounded=0"),
          good.replace("returned=0026 before=2 after=2 bounded=1",
                       "returned=0027 before=2 after=2 bounded=1"),
          good.replace("kind=pullB base=01ED","kind=pullW base=01ED"),
          good.replace("new=26F0D48226","new=26F0D48227"),
          good.replace("QA01RF064ORIGPULL","QA01RF064MISSING"),
          good.replace("QA01RF045ORIGSTACK","QA01RF045MISSING"),
          good.replace("QA01RF066ORIGCONSUMED","QA01RF066MISSING"),
          good.replace("phase=post_real_stack_getter_return","phase=inferred_bus_entry"),
          good.replace("postPC=B0EB","postPC=UNKNOWN"),
          good + "QA01RF066ORIGCONSUMED_TRUNCATED\n",
          good.replace("QA01RF066ORIGCONSUMED seq=3",
                       "prefix QA01RF066ORIGCONSUMED seq=3")
        )
        for n,bad in enumerate(trials):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    receipt.examine(bad)


if __name__=="__main__":
    unittest.main()
