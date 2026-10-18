"""RF049 complete original opcode bank census parser negative controls."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf049_sound_operand_report as rf

BASE=("QA01RF049FINAL first=6072 last=6138 total=42424 "
      "bank10=12000 bank11=12000 bank12=12000 bank13=6424 "
      "min10=8000 max10=FFFF min11=8000 max11=FFFF "
      "min12=8000 max12=FFFF min13=8000 max13=B9B1 "
      "other=0 unmapped=0 lowC774=1 lowD0B4=0 "
      "exact13C774=0 exact13D0B4=0 target_logged=1 "
      "target_overflow=0 unclosed=0")
LDA=("QA01RF049LDA ordinal=33703 frame=6124 v=159 h=992 pc=82:82F0 "
     "d=0000 ptr=110000 y=C774 ea=11C774 a0=630D a1=63D0")
S1="QA01RF049STA target=1 frame=6124 v=159 h=1012 pc=82:82F2 op=8D a0=63D0 a1=63D0"
S2="QA01RF049STA target=1 frame=6124 v=159 h=1052 pc=82:82F6 op=8D a0=63D0 a1=63D0"

def source_case():
    # RF048 original observer independently counted every completed frame.
    prior=[f"QA01RF048ORIGCOUNT frame={f} actual_lda=640"
           for f in range(6072,6138)]
    return "\n".join((*prior,BASE,LDA,S1,S2))

class RF049SourceReportTests(unittest.TestCase):
    def test_exact_all_bank_census_without_false_native_equivalence(self):
        out=rf.analyze_source(source_case())
        self.assertEqual(out["genuine_original_82F0_LDA_count"],42424)
        self.assertEqual(out["independent_RF048_prior_frame_count_receipts"],66)
        self.assertEqual(out["qualified_final_original_frame_LDA_count"],184)
        self.assertEqual(out["source_bank_counts"]["13"],6424)
        self.assertEqual(out["exact_original_full_operand_13C774"],0)
        self.assertEqual(out["source_true_LDA_followed_by_STA_2143_and_STA_2142"],1)
        self.assertFalse(out["source_vs_native_host_epoch_registered"])

    def test_fail_closed_on_missing_terminal_broken_counts_and_target(self):
        data=source_case()
        with self.assertRaisesRegex(ValueError,"exactly one"):
            rf.analyze_source(data.replace(BASE,""))
        with self.assertRaisesRegex(ValueError,"incomplete per-bank"):
            rf.analyze_source(data.replace("bank13=6424","bank13=6400"))
        with self.assertRaisesRegex(ValueError,"truncated/unpaired"):
            rf.analyze_source(data.replace("target_overflow=0","target_overflow=1"))
        with self.assertRaisesRegex(ValueError,"linkage incomplete"):
            rf.analyze_source(data.replace(S2,""))
        with self.assertRaisesRegex(ValueError,"effective operand inconsistent"):
            rf.analyze_source(data.replace("ea=11C774","ea=13C774"))
        with self.assertRaisesRegex(ValueError,"source-linked"):
            rf.analyze_source(data.replace("pc=82:82F6","pc=82:82F2"))
        with self.assertRaisesRegex(ValueError,"lack"):
            rf.analyze_source(data.replace("lowC774=1","lowC774=2"))
        with self.assertRaisesRegex(ValueError,"disagrees with final"):
            rf.analyze_source(data.replace("exact13C774=0","exact13C774=1"))
        with self.assertRaisesRegex(ValueError,"independently counted frame window incomplete"):
            rf.analyze_source(data.replace("QA01RF048ORIGCOUNT frame=6124 actual_lda=640",""))
        with self.assertRaisesRegex(ValueError,"conflicts with independent RF048"):
            rf.analyze_source(data.replace("actual_lda=640","actual_lda=2000",1))

if __name__=="__main__":unittest.main()
