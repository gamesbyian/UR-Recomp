"""RF068: real original RF066 post-call ordinals coexist with old RF063/RF064."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf063_original_sequence_report as old63
import qa01_rf064_original_pull_return_report as old64
import qa01_rf066_original_consumed_report as new66


def original_rf064_legacy():
    return (
      "QA01RF063ORIGBUS seq=1 f=1017 v=225 h=56 kind=wb"
      " bank=00 addr=01ED width=1 sampled=0026"
      " pc=80:B0E8 S=01ED phase=getset_entry\n"
      "QA01RF063ORIGCHECKPOINT seq=2 f=1017 f1=1017"
      " phase=post_real_nmi_push stack=26F0D48226 v=225 h=65 pc=80:B0EB\n"
      "QA01RF044ORIGNMI f=1017 f1=1017 pc=82D4F0"
      " S0=01F0 S1=01ED old=8197005526 new=26F0D48226\n"
      "QA01RF063ORIGBUS seq=3 f=1018 v=225 h=70 kind=rb"
      " bank=00 addr=01ED width=1 sampled=0026"
      " pc=80:B0EB S=01ED phase=getset_entry\n"
      "QA01RF045ORIGSTACK seq=1 f=1018 v=225 h=80"
      " kind=pullB addr=01ED width=1 value=0026 sp0=01EC sp1=01ED pc=80:B0EB\n"
      "QA01RF064ORIGPULL f=1018 v=225 h=80 kind=pullB"
      " base=01ED width=1 returned=0026 before=2 after=3 unique=1 pc=80:B0EB\n"
    )


def genuine_rf066_augmented():
    # Source's original RF063 getset read-entry observer remains incomplete.
    # True RF066 evidence is at the *post-return* phase, not a bus entry.
    old=original_rf064_legacy()
    old="\n".join(x for x in old.splitlines()
                  if not x.startswith("QA01RF063ORIGBUS seq=3"))+"\n"
    old=old.replace("before=2 after=3 unique=1","before=2 after=2 unique=0")
    witness=("QA01RF066ORIGCONSUMED seq=3 f=1018 v=225 h=80"
             " phase=post_real_stack_getter_return"
             " kind=pullB base=01ED width=1 returned=0026"
             " before=2 after=2 bounded=1 postPB=80 postPC=B0EB\n")
    return old.replace("QA01RF045ORIGSTACK seq=1",witness+"QA01RF045ORIGSTACK seq=1")


class BackwardsCompatibleSourceTruth(unittest.TestCase):
    def test_real_RF066_sequence_keeps_getset_writes_and_post_return_separate(self):
        a=genuine_rf066_augmented()
        v=old63.inspect(a)
        self.assertEqual(v["sequenced_original_bus_entries"],1)
        self.assertEqual(v["sequenced_real_postcall_returns"],1)
        self.assertEqual(v["checkpoint_seq"],2)
        self.assertEqual(v["checkpoint_actual_unmasked_stack_01ed_to_01f1"],"26F0D48226")
        self.assertTrue(v["original_getset_read_entries_not_inferred_from_postcall"])
        self.assertFalse(v["eligible_for_qa01_causal_window"])
        old=old64.check(a)
        self.assertEqual(old["sequenced_original_bus_entries"],1)
        self.assertEqual(old["post_call_actual_original_pull_count"],1)
        self.assertEqual(old["actual_returns_with_unique_source_bus_entry"],0)
        self.assertEqual(old["ambiguous_or_reentrant_original_pulls"],1)
        self.assertEqual(old["accepted_USA_events"],0)
        current=new66.examine(a)
        self.assertEqual(current["total_sequenced_original_source_events"],3)
        self.assertEqual(current["actual_original_post_getter_return_count"],1)
        self.assertEqual(current["sequenced_source_getset_read_entries"],0)

    def test_uninstrumented_legacy_RF064_still_qualifies_old_stream(self):
        old=original_rf064_legacy()
        self.assertEqual(old63.inspect(old)["sequenced_real_postcall_returns"],0)
        self.assertEqual(old64.check(old)["actual_returns_with_unique_source_bus_entry"],1)

    def test_out_of_order_or_fabricated_postcall_is_not_ignored(self):
        good=genuine_rf066_augmented()
        defects=(
          good.replace("QA01RF066ORIGCONSUMED seq=3","QA01RF066ORIGCONSUMED seq=4"),
          good.replace("before=2 after=2 bounded=1","before=2 after=4 bounded=1"),
          good.replace("bounded=1 postPB","bounded=0 postPB"),
          good.replace("phase=post_real_stack_getter_return","phase=guest_bus_entry"),
          good.replace("kind=pullB base=01ED width=1","kind=pullW base=01ED width=1"),
          good.replace("base=01ED width=1 returned=0026 before=2 after=2 bounded=1",
                       "base=01E0 width=1 returned=0026 before=2 after=2 bounded=1"),
          good.replace("postPB=80 postPC=B0EB","postPB=ZZ postPC=B0EB"),
          good+"QA01RF066ORIGCONSUMED_TRUNCATED\n",
          good.replace("QA01RF066ORIGCONSUMED seq=3",
                       "other QA01RF066ORIGCONSUMED seq=3"),
        )
        for i,bad in enumerate(defects):
            with self.subTest(i=i),self.assertRaises(ValueError):
                old63.inspect(bad)


if __name__=="__main__":
    unittest.main()
