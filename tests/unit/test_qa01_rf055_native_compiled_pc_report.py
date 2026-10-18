"""RF055: independently executed 65816 PC evidence must fail closed."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf055_native_compiled_pc_report as rf
SC="Snd_UploadBlockList_82EF_M1X0"
def pc(addr,clock,A):
    return (f"QA01RF055NATIVEPC pc={addr} scope={SC} frame=6124 "
            f"master={clock} A={A} Y=C774 D=0000 dp63=00 dp64=00 dp65=11")
def bus():
    return (f"QA01RF054NATIVEBUS kind=read8 seq=1 frame=6124 "
            f"master=105 addr=11C774 A=630D Y=C774 D=0000 "
            f"dp63=00 dp64=00 dp65=11 scope={SC}")
def writer(seq,port,value,clock,A):
    return (f"QA01RF054NATIVE kind=writer seq={seq} frame=6124 "
            f"master={clock} addr={port} val={value} PB=82 DB=80 "
            f"A={A} Y=C774 D=0000 dp63=00 dp64=00 dp65=11 scope={SC}")
ROWS=(pc("8282F0",100,"630D"),bus(),pc("8282F2",120,"63D0"),
      writer(1,"002143","00D0",130,"63D0"),
      pc("8282F6",140,"D063"),writer(2,"002142","0063",160,"D063"))
class RF055NativePC(unittest.TestCase):
    def test_true_opcodes_scope_bus_port_and_clock(self):
        r=rf.inspect("\n".join(ROWS),expected_transfers=1)
        self.assertEqual(r["executed_instruction_PC_records"],3)
        self.assertEqual(r["exact_native_compiled_transfer_count"],1)
        self.assertEqual(r["unique_source_matched_11C774_to_D0_63_executed_PC_chain"]["native_CPU_master_clocks"],[100,105,120,130,140,160])
        self.assertFalse(r["original_native_absolute_CPU_SP_C_clock_phase_proven"])
        self.assertEqual(r["event_admission_credit"],0)
    def test_rejects_missing_reordered_or_spoofed_PC(self):
        base=list(ROWS)
        for label,modified,reason in (
            ("missing-PC",base[:2]+base[3:],"incomplete"),
            ("wrong-PC",base[:2]+[base[2].replace("8282F2","8282F0")]+base[3:],"incorrect emitted"),
            ("wrong-context",base[:2]+[base[2].replace("A=63D0","A=63D1")]+base[3:],"A differs"),
            ("clock-backwards",base[:2]+[base[2].replace("master=120","master=99")]+base[3:],"clock regression"),
            ("ROM-drift",base[:1]+[base[1].replace("11C774","11C775")]+base[2:],"effective operand"),
            ("wrong-native-source",base[:1]+[base[1].replace("seq=1","seq=2")]+base[2:],"ordinal"),
            ("port-tamper",base[:-1]+[base[-1].replace("val=0063","val=0064")],"published value"),
            ("wrong-PC-frame",base[:1]+[base[1].replace("frame=6124","frame=6125")]+base[2:],"provenance"),
        ):
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError,reason):
                    rf.inspect("\n".join(modified),expected_transfers=1)
    def test_truncation_and_wrong_count_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"truncated"):
            rf.inspect("\n".join(ROWS)+"\nQA01RF054NATIVEBUS_TRUNCATED",expected_transfers=1)
        with self.assertRaisesRegex(ValueError,"count changed"):
            rf.inspect("\n".join(ROWS),expected_transfers=656)
if __name__=="__main__":unittest.main()
