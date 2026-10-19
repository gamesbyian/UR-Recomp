"""RF073: source/native real NMI bracket observer does not infer full CPU PC."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf073_native_nmi_brackets as rf

def fixture():
    seq=0
    lines=[]
    source=[]
    for frame in rf.FRAMES:
        master=100000+1000*(frame-1017)
        def add(stage,rest):
            nonlocal seq
            seq+=1
            lines.append(f"QA01RF047NATIVE seq={seq} stage={stage} f={frame} {rest}")
        add("entry",f"resume=82D4EE vector=008588 PB=83 P=26 S=01F0 emu=0 master={master} beamMaster={master-82} beamV=225 beamH=0 stack=81970027")
        add("after_push",f"resume=82D4EE vector=008588 PB=83 P=26 S=01EC emu=0 master={master} beamMaster={master-82} beamV=225 beamH=0 stack=26EED482")
        add("read",f"bank=00 addr=01ED width=1 value=0026 PB=80 P=26 S=01ED master={master+14} beamV=226 beamH=322 nmi=1")
        add("compiled_rti",f"opcodePC=008588 returnPC=808588 P=26 S=01F0 master={master+14} beamV=226 beamH=322")
        add("handler_return",f"resume=82D4EE vector=008588 PB=80 P=26 S=01F0 emu=0 master={master+14} beamMaster={master} beamV=226 beamH=322 stack=26EED482")
        add("read",f"bank=00 addr=01F1 width=1 value=0026 PB=82 P=26 S=01F1 master={master+20} beamV=226 beamH=322 nmi=0")
        extras=299 if frame<1025 else 295
        for j in range(extras):
            add("read",f"bank=00 addr=01EF width=1 value=002A PB=81 P=26 S=01EF master={master+21+j} beamV=230 beamH=40 nmi=0")
        pc="82D4F0" if (frame-1017) in (0,2,4,6) else "82D4EE"
        low=pc[-2:]
        source.append(f"QA01RF044ORIGNMI f={frame} f1={frame} pc={pc} S0=01F0 S1=01EC old=8197005526 new=26{low}D48226")
    assert seq==2741
    return "\n".join(lines)+"\n","\n".join(source)+"\n"

class NativeNMIBracket(unittest.TestCase):
    def test_full_2741_native_observation_and_nine_real_status_reads(self):
        native,source=fixture()
        result=rf.inspect(native,source)
        self.assertEqual(result["native_RF047_event_count"],2741)
        self.assertEqual(result["authentic_native_NMI_frame_count"],9)
        self.assertEqual(result["native_compiled_NMI_brackets_with_one_actual_status_helper_read"],9)
        self.assertEqual(result["source_original_native_NMI_saved_PC_low_differences"],4)
        self.assertEqual(result["native_saved_PC_or_PB_helper_reads_between_push_and_compiled_RTI"],0)
        self.assertFalse(result["original_native_same_intra_frame_semantic_phase_proven"])
        self.assertFalse(result["compiled_RTI_opcodePC_field_is_qualified_actual_fetch_PC"])
        self.assertEqual(result["accepted_complete_USA_events"],0)

    def test_other_logger_prefix_does_not_delete_one_atomic_native_event(self):
        n,s=fixture()
        n=n.replace("QA01RF047NATIVE seq=4 ", "QA01RF044NATIVEREAD_PARTIALQA01RF047NATIVE seq=4 ",1)
        self.assertEqual(rf.inspect(n,s)["native_RF047_compiled_RTI_events_with_prefix_fragments"],1)

    def test_nmi_missing_or_forged_events_are_not_promoted(self):
        n,s=fixture()
        variants=(
            n.replace("seq=3 stage=read","seq=4 stage=read",1),
            n.replace("seq=3 stage=read f=1017 bank=00 addr=01ED",
                      "seq=3 stage=read f=1017 bank=00 addr=01EE",1),
            n.replace("seq=4 stage=compiled_rti","seq=4 stage=interp_rti",1),
            n.replace("seq=4 stage=compiled_rti f=1017 opcodePC=008588 returnPC=808588 P=26 S=01F0",
                      "seq=4 stage=compiled_rti f=1017 opcodePC=008588 returnPC=808588 P=26 S=01ED",1),
            n.replace("seq=3 stage=read f=1017 bank=00 addr=01ED width=1 value=0026",
                      "seq=3 stage=read f=1017 bank=00 addr=01ED width=1 value=0027",1),
            n.replace("seq=3 stage=read f=1017", "seq=3 stage=read f=1016",1),
            n+"QA01RF047NATIVE_TRUNCATED\n",
            n.replace("QA01RF047NATIVE seq=4", "QA01RF047NATIVE seq=4",1).replace(
                "QA01RF047NATIVE seq=5 ", "QA01RF047NATIVE seq=4 ",1)
        )
        for i,altered in enumerate(variants):
            with self.subTest(i=i),self.assertRaises(ValueError):
                rf.inspect(altered,s)

    def test_source_original_PB_PC_saved_bytes_cannot_be_rewritten(self):
        n,s=fixture()
        for altered in (
            s.replace("new=26F0D48226","new=26F1D48226",1),
            s.replace("S1=01EC","S1=01ED",1),
            s.replace("pc=82D4F0","pc=82D4FF",1),
            s.replace("QA01RF044ORIGNMI f=1017","QA01RF044ORIGNMI f=1018",1)):
            with self.subTest(source=altered[:80]),self.assertRaises(ValueError):
                rf.inspect(n,altered)

    def test_a_nonmatching_archive_cannot_be_called_authentic(self):
        with self.assertRaisesRegex(ValueError,"SHA256 mismatch"):
            rf.authenticated_case(Path(__file__))

if __name__=="__main__":
    unittest.main()
