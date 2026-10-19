"""RF063 staging and standalone source-order receipt: strict, no read promotion."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf044_stack_bus_witness as rf44
import qa01_rf045_source_stack_macro_witness as rf45
import qa01_rf063_original_shared_sequence as probe
import qa01_rf063_original_sequence_report as report


def fixture():
    # Exact upstream RF044/045 staged segments; no outside ROM needed.
    src=rf44.ORIG_HELPER
    executor='#include "movie.h"\nvoid original_nmi() {\n' + rf44.NMI_NEW + '\n}\n'
    macros=rf45.STAMP + '\n'
    return src,executor,macros


def example():
    return ('QA01RF063ORIGBUS seq=1 f=1017 v=225 h=56 kind=wb'
            ' bank=00 addr=01ED width=1 sampled=0026'
            ' pc=80:B0E8 S=01ED phase=getset_entry\n'
            'QA01RF063ORIGCHECKPOINT seq=2 f=1017 f1=1017'
            ' phase=post_real_nmi_push stack=2600EE0000'
            ' v=225 h=65 pc=80:B0EB\n'
            'QA01RF044ORIGNMI f=1017 f1=1017 pc=82D4F0 S0=01F0 S1=01ED'
            ' old=0000000000 new=2600EE0000\n'
            'QA01RF063ORIGBUS seq=3 f=1018 v=225 h=70 kind=rb'
            ' bank=00 addr=01ED width=1 sampled=0026'
            ' pc=80:B0EB S=01ED phase=getset_entry\n')


class StagedOriginal(unittest.TestCase):
    def test_research_patch_is_bounded_without_duplicating_guest_calls(self):
        getset,executor,ops=fixture()
        newg,newx=probe.patch(getset,executor,ops)
        self.assertIn(probe.STAMP,newg)
        self.assertIn(probe.STAMP,newx)
        self.assertEqual(newg.count(probe.BUS_NOTE),1)
        self.assertEqual(newx.count(probe.CHECKPOINT),1)
        self.assertEqual(newx.count('S9xOpcode_NMI();'),1)
        self.assertEqual(newg.count('S9xGetByte('),getset.count('S9xGetByte('))
        self.assertEqual(newg.count('S9xSetByte('),getset.count('S9xSetByte('))
        self.assertIn('phase=getset_entry',newg)
        self.assertIn('post_real_nmi_push',newx)
        self.assertIn('Memory.RAM[0x01f1]',newx)
        self.assertIn('rf044_f0 == 1017u',newx)
        self.assertIn('extern unsigned long long ur_rf063_source_bus_seq;',newg)
        self.assertIn('unsigned long long ur_rf063_source_bus_seq = 0;',newx)

    def test_rejects_absent_prerequisites_shifted_anchor_and_double_install(self):
        getset,executor,ops=fixture()
        for triple in ((getset,executor,'no RF045'),
                       (getset.replace(rf44.STAMP,'old'),executor,ops),
                       (getset,executor.replace(probe.NMI_ANCHOR,
                                                 probe.NMI_ANCHOR.replace('if(rf044_nmi)','if(other)')),ops),
                       (getset,executor.replace(probe.GLOBAL_ANCHOR,''),ops)):
            with self.subTest(triple=triple[-1][:15]):
                with self.assertRaises(ValueError):
                    probe.patch(*triple)
        newg,newx=probe.patch(getset,executor,ops)
        with self.assertRaisesRegex(ValueError,"already staged"):
            probe.patch(newg,newx,ops)


class OriginalOrderReceipt(unittest.TestCase):
    def test_retains_unmasked_five_byte_source_checkpoint_only(self):
        result=report.inspect(example())
        self.assertEqual(result["sequenced_original_bus_entries"],2)
        self.assertEqual(result["checkpoint_seq"],2)
        self.assertEqual(result["checkpoint_actual_unmasked_stack_01ed_to_01f1"],"2600EE0000")
        self.assertTrue(result["ordinal_contiguous_across_original_bus_and_checkpoint"])
        self.assertFalse(result["actual_bus_read_return_value_for_all_events_proven"])
        self.assertFalse(result["eligible_for_qa01_causal_window"])
        self.assertEqual(result["accepted_USA_events"],0)

    def test_rejects_gaps_forged_checkpoint_truncation_or_bad_origin(self):
        normal=example()
        variants=(
            normal.replace("seq=3 f=1018","seq=4 f=1018"),
            normal.replace("seq=3 f=1018","seq=2 f=1018"),
            normal.replace("stack=2600EE0000","stack=2700EE0000"),
            normal.replace("phase=post_real_nmi_push","phase=guess"),
            normal.replace("sampled=0026","sampled=GGGG"),
            normal.replace("kind=rb","kind=diagnostic"),
            normal.replace("bank=00 addr=01ED","bank=60 addr=01ED"),
            normal.replace("seq=2 f=1017","seq=2 f=1018"),
            normal.replace("QA01RF044ORIGNMI","QA01RF044NO_NMI"),
            normal + "QA01RF063ORIGBUS_TRUNCATED\n",
            normal.replace("QA01RF063ORIGBUS seq=3","other_prefix QA01RF063ORIGBUS seq=3"),
        )
        for i,bad in enumerate(variants):
            with self.subTest(i=i):
                with self.assertRaises(ValueError):
                    report.inspect(bad)

    def test_refuses_pre_RF063_archive_and_missing_getset_rows(self):
        with self.assertRaises(ValueError):
            report.inspect('QA01RF044ORIGNMI f=1017 new=2600EE0000')
        with self.assertRaises(ValueError):
            report.inspect(example().replace('QA01RF063ORIGBUS','RF044BUS'))


if __name__=="__main__":
    unittest.main()
