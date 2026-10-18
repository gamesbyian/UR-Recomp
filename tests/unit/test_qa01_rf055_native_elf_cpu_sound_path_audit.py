"""RF055 independent executable path and real CPU bus evidence stays fail closed."""
from pathlib import Path
import sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf055_native_elf_cpu_sound_path_audit as rf

class RF055ELFAudit(unittest.TestCase):
    def test_compiled_path_requires_live_mode_exact_call_targets(self):
        nm="00000000006aea70 t Snd_UploadBlockList_82EF_M1X0.part.0\n"
        asm="\n".join(
            f"  {pc:x}:\t90\t{op}" for pc,op in rf.PATH
        ) + "\n  6affff:\t90\tcall   3e040 <cpu_read8_paced>\n"
        out=rf.inspect_elf_text(nm,asm)
        self.assertEqual(len(out),10)
        self.assertEqual(out[4]["x86_va"],"0x6aebcf")
        self.assertIn("0x2143",out[5]["operation"])
        self.assertIn("0x2142",out[8]["operation"])
        with self.assertRaisesRegex(ValueError,"function missing"):
            rf.inspect_elf_text(nm.replace("82EF_M1X0","82EF_M0X0"),asm)
        with self.assertRaisesRegex(ValueError,"call path changed"):
            rf.inspect_elf_text(nm,asm.replace("mov    edx,0x2143","mov    edx,0x2144"))
        with self.assertRaisesRegex(ValueError,"competing helper"):
            rf.inspect_elf_text(nm,asm.replace(
                "call   3e040 <cpu_read8_paced>","call   3e040 <cpu_read16_paced>"))
    def make_real_bus_rows(self):
        rows=[]
        base=2188739002-491*250
        for i in range(656):
            y=0xC589+i
            master=base+i*250
            rows.extend((
                f"QA01RF054NATIVEBUS kind=read8 seq={i+1} frame=6124 "
                f"master={master} addr=11{y:04X} A=630D Y={y:04X} D=0000 "
                f"dp63=00 dp64=00 dp65=11 scope={rf.SCOPE}",
                f"QA01RF054NATIVE kind=writer seq={2*i+1} frame=6124 "
                f"master={master+30} addr=002143 val=00D0 A=63D0 Y={y:04X} D=0000 "
                f"dp63=00 dp64=00 dp65=11 scope={rf.SCOPE}",
                f"QA01RF054NATIVE kind=writer seq={2*i+2} frame=6124 "
                f"master={master+80} addr=002142 val=0063 A=D063 Y={y:04X} D=0000 "
                f"dp63=00 dp64=00 dp65=11 scope={rf.SCOPE}"
            ))
        return "\n".join(rows)
    def test_all_656_real_CPU_bus_and_1312_writes(self):
        records=self.make_real_bus_rows()
        reads,writes=rf.genuine_cpu_records(records)
        self.assertEqual(len(reads),656)
        self.assertEqual(len(writes),1312)
        self.assertEqual(reads[491]["addr"],"11C774")
        for label,dirty,error in (
            ("operand",records.replace("addr=11C774","addr=13C774"),"operand/ordinal"),
            ("port",records.replace("addr=002143","addr=002144",1),"pointer or APU"),
            ("phase",records.replace("master="+str(2188739032),"master="+str(2188739033)),"timing"),
            ("wrong_scope",records.replace("scope="+rf.SCOPE,"scope=other",1),"scope/frame"),
            ("truncation",records+"\nQA01RF054NATIVEBUS_TRUNCATED","truncated"),
            ("missing",records.split("\n",1)[1],"counts incomplete"),
        ):
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError,error):
                    rf.genuine_cpu_records(dirty)

if __name__=="__main__": unittest.main()
