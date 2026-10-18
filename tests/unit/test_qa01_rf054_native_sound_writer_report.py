"""RF054 reporter: bus helper versus ROM mapping, genuine native CPU writer."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf054_native_sound_writer_report as rf

def event(kind,seq,master,addr,val,scope="Snd_UploadBlock_80D1_M1X0"):
    return (f"QA01RF054NATIVE kind={kind} seq={seq} frame=6124 master={master} "
            f"addr={addr} val={val} PB=82 DB=11 D=0000 Y=C774 A=63D0 "
            f"dp63=00 dp64=00 dp65=11 scope={scope}")
def bus(seq,master,addr):
    return (f"QA01RF054NATIVEBUS kind=read8 seq={seq} frame=6124 master={master} "
            f"addr={addr} A=630D Y=C774 D=0000 dp63=00 dp64=00 dp65=11 "
            f"scope=Snd_UploadBlock_80D1_M1X0")

M=event("rom-map",1,100,"11C774","0000")
B=bus(1,105,"11C774")
W1=event("writer",1,110,"002143","00D0")
W2=event("writer",2,160,"002142","0063")

class RF054ActualWriter(unittest.TestCase):
    def test_actual_publication_and_true_helper_do_not_infer_opcodes(self):
        out=rf.inspect("\n".join((M,B,W1,W2)))
        self.assertEqual(out["genuine_late_D0_63_CPU_writer_pair_count"],1)
        self.assertEqual(out["native_actual_CPU_ROM_bus_helper_read_count"],1)
        self.assertEqual(out["native_ROM_pointer_mapping_request_count"],1)
        self.assertEqual(out["mapping_requests_prior_to_writer_20000_master_clock_window"][0]["addr"],"11C774")
        self.assertFalse(out["native_compiled_65816_instruction_PC_proven"])
        self.assertFalse(out["original_11C774_operand_equals_native_effective_ROM_operand_proven"])
        self.assertFalse(out["source_native_CPU_APU_publication_clock_registered"])
    def test_no_invented_transfer_when_bytes_or_identity_missing(self):
        data="\n".join((M,B,W1,W2))
        for name,wrong,expect in (
            ("no original writer",data.replace("val=0063","val=0064"),"absent/nonunique"),
            ("repeated pair",data+"\n"+event("writer",3,170,"002143","00D0")+"\n"+event("writer",4,220,"002142","0063"),"absent/nonunique"),
            ("malformed read",data.replace("addr=11C774 A=","addr=ZZC774 A="),"outside qualified"),
            ("missing helper sequence",data.replace("kind=read8 seq=1","kind=read8 seq=3"),"lost or duplicated"),
            ("truncated",data+"\nQA01RF054NATIVE_TRUNCATED kind=rom-map","truncated"),
            ("real-bus-truncated",data+"\nQA01RF054NATIVEBUS_TRUNCATED","truncated"),
        ):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError,expect):
                    rf.inspect(wrong)
    def test_real_bus_helper_not_mistaken_for_rom_map(self):
        out=rf.inspect("\n".join((M,W1,W2)))
        self.assertEqual(out["native_actual_CPU_ROM_bus_helper_read_count"],0)
        self.assertTrue(out["native_ROM_pointer_mapping_is_not_proof_of_dereference"])
if __name__=="__main__":unittest.main()
