"""RF067: real original RF045 macro ancestry, no inferred unobserved bus reads."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf067_original_macro_lineage as rf


def row(seq,kind,addr,width,value,sp0,sp1,frame=1017,pc="82:D4F0"):
    return (f"QA01RF045ORIGSTACK seq={seq} f={frame} v=225 h=34"
            f" kind={kind} addr={addr:04X} width={width} value={value:04X}"
            f" sp0={sp0:04X} sp1={sp1:04X} pc={pc}\n")


def fixture():
    return (row(1,"pullW",0x01f0,2,0x9141,0x01ef,0x01f1)
            +row(2,"pushW",0x01f0,2,0x914e,0x01f1,0x01ef)
            +row(3,"pullW",0x01f0,2,0x914e,0x01ef,0x01f1)
            +row(4,"pushB",0x01ed,1,0x26,0x01ed,0x01ec)
            +row(5,"pullB",0x01ed,1,0x26,0x01ec,0x01ed,
                 pc="80:B0EB"))


class TrueSourceMacroLineage(unittest.TestCase):
    def test_initial_unknown_retained_and_only_true_prior_writes_accepted(self):
        a=rf.parse(fixture())
        r=rf.audit(a)
        self.assertEqual(r["total_actual_stack_macro_operations"],5)
        self.assertEqual(r["total_actual_macro_pulls"],3)
        self.assertEqual(r["pulls_with_unobserved_initial_byte_or_writer"],1)
        self.assertEqual(r["pulls_with_all_bytes_preceded_by_a_macro_writer_and_exact_return"],2)
        self.assertEqual(r["pulls_with_conflicting_last_macro_writer"],0)
        self.assertEqual(r["source_status_01ed_value_counts"],{"26":1})
        self.assertEqual(r["source_status_01ed_pulls"][0]["preceding_macro_write"]["source_seq"],4)
        self.assertFalse(r["stack_writer_and_reader_population_complete_outside_RF045_macros"])
        self.assertFalse(r["causal_window_or_all_USA_event_admission"])
        self.assertEqual(r["accepted_USA_events"],0)

    def test_preserves_raw_actual_return_difference_without_exemption(self):
        bad=fixture().replace("seq=5 f=1017 v=225 h=34 kind=pullB addr=01ED width=1 value=0026",
                              "seq=5 f=1017 v=225 h=34 kind=pullB addr=01ED width=1 value=0027")
        r=rf.audit(rf.parse(bad))
        self.assertEqual(r["pulls_with_conflicting_last_macro_writer"],1)
        self.assertEqual(r["pulls_with_all_bytes_preceded_by_a_macro_writer_and_exact_return"],1)
        self.assertEqual(r["raw_conflicting_original_macro_pulls"][0]["raw_differences"][0]["source_writer_seq"],4)

    def test_multi_byte_last_writer_tracks_each_byte_not_stale_prior_word(self):
        # The new PUSHB replaces the low byte of the prior PUSHW. PULLW
        # should return 0x914F, not 0x914E.
        new=(row(1,"pushW",0x01f0,2,0x914e,0x01f1,0x01ef)
             +row(2,"pushB",0x01f0,1,0x4f,0x01f0,0x01ef)
             +row(3,"pullW",0x01f0,2,0x914f,0x01ef,0x01f1))
        report=rf.audit(rf.parse(new))
        self.assertEqual(report["pulls_with_all_bytes_preceded_by_a_macro_writer_and_exact_return"],1)
        self.assertEqual(report["pulls_with_conflicting_last_macro_writer"],0)

    def test_rejects_out_of_order_macros_sp_drift_and_overflow(self):
        good=fixture()
        defects=(
            good.replace("seq=5 f=1017","seq=7 f=1017"),
            good.replace("seq=5 f=1017","seq=4 f=1017"),
            good.replace("seq=4 f=1017","seq=4 f=1026"),
            good.replace("seq=4 f=1017","seq=4 f=1017").replace("sp1=01EC pc=82:D4F0","sp1=01ED pc=82:D4F0"),
            good.replace("kind=pullW addr=01F0 width=2","kind=pullW addr=01F0 width=1"),
            good.replace("kind=pushB addr=01ED","kind=pushB addr=01E2"),
            good.replace("QA01RF045ORIGSTACK seq=5","foo QA01RF045ORIGSTACK seq=5"),
            good + "QA01RF045ORIGSTACK_TRUNCATED\n"
        )
        for i,bad in enumerate(defects):
            with self.subTest(i=i),self.assertRaises(ValueError):
                rf.parse(bad)

    def test_unverified_case_zip_cannot_become_authentic_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"forged.zip"
            path.write_bytes(b"not a genuine case")
            with self.assertRaisesRegex(ValueError,"digest drift"):
                rf.authenticated_case(path)


if __name__=="__main__":
    unittest.main()
