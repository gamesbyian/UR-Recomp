"""RF064 never converts a macro return into an inferred read or bus call."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf045_source_stack_macro_witness as rf45
import qa01_rf064_original_post_call_pull as patcher
import qa01_rf064_original_pull_return_report as audit

def source_fixture():
    return ('#include "cpumacro.h"\n'
            + rf45.HELPER + '\n' + rf45.PULL_B_NEW + '\n' + rf45.PULL_NEW)

def genuine_rows():
    return (
      "QA01RF063ORIGBUS seq=1 f=1017 v=225 h=56 kind=wb"
      " bank=00 addr=01ED width=1 sampled=0026 pc=80:B0E8 S=01ED phase=getset_entry\n"
      "QA01RF063ORIGCHECKPOINT seq=2 f=1017 f1=1017"
      " phase=post_real_nmi_push stack=2600EE0000"
      " v=225 h=65 pc=80:B0EB\n"
      "QA01RF044ORIGNMI f=1017 f1=1017 pc=82D4F0 S0=01F0 S1=01ED"
      " old=0000000000 new=2600EE0000\n"
      "QA01RF063ORIGBUS seq=3 f=1018 v=225 h=70 kind=rb"
      " bank=00 addr=01ED width=1 sampled=0026 pc=80:B0EB S=01ED phase=getset_entry\n"
      "QA01RF045ORIGSTACK seq=1 f=1018 v=225 h=80 kind=pullB"
      " addr=01ED width=1 value=0026 sp0=01EC sp1=01ED pc=80:B0EB\n"
      "QA01RF064ORIGPULL f=1018 v=225 h=80 kind=pullB base=01ED"
      " width=1 returned=0026 before=2 after=3 unique=1 pc=80:B0EB\n"
    )

class OriginalPullPatch(unittest.TestCase):
    def test_macro_returns_are_real_and_purely_observational(self):
        original=source_fixture()
        modified=patcher.patch(original)
        self.assertIn(patcher.STAMP,modified)
        self.assertEqual(modified.count('ur_rf064_post_pull("pullB"'),1)
        self.assertEqual(modified.count('ur_rf064_post_pull("pullW"'),1)
        for x in ("S9xGetByte(", "S9xGetWord(", "S9xSetByte(", "S9xSetWord("):
            self.assertEqual(original.count(x),modified.count(x))
        self.assertIn('const unsigned long long rf064_before',modified)
        self.assertIn('const unsigned long long rf064_after',modified)
        self.assertIn('const unsigned joined = after == before + 1u',modified)
        self.assertEqual(modified.count('ur_rf045_stack_note("pullB"'),1)
        self.assertEqual(modified.count('ur_rf045_stack_note("pullW"'),1)
        self.assertIn('(uint16)(ur_rf045_sp0+1)',modified)
        self.assertNotIn('(uint16)(rf045_sp0+1)',modified)

    def test_missing_prerequisites_drift_and_restage_fail_closed(self):
        original=source_fixture()
        for bad in (original.replace(rf45.STAMP,'not_RF045'),
                    original.replace(patcher.HEADER_ANCHOR,''),
                    original.replace(patcher.PULL_B_GET,'        b=0; \\\n'),
                    original.replace(rf45.PULL_NEW,rf45.PULL_OLD)):
            with self.subTest(case=bad[:30]):
                with self.assertRaises(ValueError):
                    patcher.patch(bad)
        with self.assertRaisesRegex(ValueError,"already"):
            patcher.patch(patcher.patch(original))

class RealConsumedReturn(unittest.TestCase):
    def test_source_getset_exact_one_and_actual_macro_return(self):
        output=audit.check(genuine_rows())
        self.assertEqual(output["post_call_actual_original_pull_count"],1)
        self.assertEqual(output["actual_returns_with_unique_source_bus_entry"],1)
        self.assertTrue(output["original_return_join_all_qualified"])
        self.assertEqual(output["ambiguous_or_reentrant_original_pulls"],0)
        self.assertFalse(output["source_native_full_memory_causal_ready"])
        self.assertEqual(output["accepted_USA_events"],0)

    def test_original_boundary_overlapping_word_pull_is_not_discarded(self):
        original=genuine_rows()
        altered=(original
          .replace('kind=rb bank=00 addr=01ED width=1 sampled=0026',
                   'kind=rw bank=00 addr=01EC width=2 sampled=0026')
          .replace('kind=pullB addr=01ED width=1 value=0026',
                   'kind=pullW addr=01EC width=2 value=0026')
          .replace('kind=pullB base=01ED width=1 returned=0026',
                   'kind=pullW base=01EC width=2 returned=0026'))
        qualified=audit.check(altered)
        self.assertEqual(qualified["actual_returns_with_unique_source_bus_entry"],1)

    def test_multiple_entries_inside_pull_are_preserved_as_ambiguous(self):
        altered=genuine_rows().replace('before=2 after=3 unique=1','before=1 after=3 unique=0')
        output=audit.check(altered)
        self.assertEqual(output["actual_returns_with_unique_source_bus_entry"],0)
        self.assertEqual(output["ambiguous_or_reentrant_original_pulls"],1)
        self.assertFalse(output["original_return_join_all_qualified"])

    def test_rejects_false_pc_bus_return_or_unmasked_raw_corruption(self):
        good=genuine_rows()
        cases=(
          good.replace('before=2 after=3 unique=1','before=1 after=3 unique=1'),
          good.replace('returned=0026','returned=0027'),
          good.replace('sampled=0026 pc=80:B0EB','sampled=0027 pc=80:B0EB'),
          good.replace('kind=rb','kind=wb'),
          good.replace('base=01ED width=1 returned','base=01EE width=1 returned'),
          good.replace('after=3 unique=1','after=5 unique=1'),
          good.replace('new=2600EE0000','new=2700EE0000'),
          good.replace('QA01RF045ORIGSTACK','QA01RF045MISSING'),
          good.replace('QA01RF063ORIGCHECKPOINT','QA01RF063OTHER'),
          good + ('QA01RF045ORIGSTACK seq=2 f=1018 v=225 h=80 kind=pullB'
                  ' addr=01ED width=1 value=0026 sp0=01EC sp1=01ED pc=80:B0EB\n'),
          good + 'QA01RF064ORIGPULL_TRUNCATED\n',
        )
        for i,bad in enumerate(cases):
            with self.subTest(case=i):
                with self.assertRaises(ValueError):
                    audit.check(bad)

if __name__=="__main__": unittest.main()
