"""ROM-free RF083 original genuine writer source patch checks."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf083_original_sound_dp_first_writer as m

def source():
    return (m.HEADER+"void cpu(){\n"+
      "Op = CPU.PCBase[Registers.PCw];\n"+
      "Op = S9xGetByte(Registers.PBPC);\n"+m.OP+"\n}\n")
def setter():
    return m.BYTE+"  actually_map(Byte,Address);\n}\n"

class RF083Source(unittest.TestCase):
    def test_true_fetch_and_setter_identity_with_no_extra_guest_accesses(self):
        a,b=m.patch(source(),setter())
        self.assertEqual(a.count(m.STAMP),1)
        self.assertEqual(a.count(m.OP),1)
        self.assertEqual(b.count(m.BYTE),1)
        self.assertLess(a.index("rf083_pre(Op);"),a.index(m.OP))
        self.assertLess(a.index(m.OP),a.index("rf083_post();"))
        self.assertLess(b.index("rf083_setbyte_entry(Byte,Address);"),
                        b.index("actually_map(Byte,Address);"))
        for marker in ("setter_entry","opcode_delta","QA01RF083ORIG_HEART",
                       "QA01RF083ORIG_TRUNCATED","clock=original_cpu",
                       "setterAddr=%06X","pc=%06X","6069u","6079u"):
            self.assertIn(marker,a)
        for fn in ("S9xGetByte(","S9xGetWord(","S9xSetByte(","S9xSetWord("):
            self.assertNotIn(fn,m.C)

    def test_source_drift_and_partial_patch_refused(self):
        a,b=m.patch(source(),setter())
        for x,y in ((a,b),(source()+m.STAMP,setter()),
                    (source(),setter()+"rf083_setbyte_entry"),
                    (source().replace(m.OP,"fake()"),setter()),
                    (source().replace("Op = CPU.PCBase[Registers.PCw];",""),setter()),
                    (source().replace("Op = S9xGetByte(Registers.PBPC);",""),setter()),
                    (source(),setter().replace(m.BYTE,"fake_setter()"))):
            with self.subTest(size=(len(x),len(y))):
                with self.assertRaises(ValueError):m.patch(x,y)

    def test_ambiguous_callsites_refused(self):
        for x,y in ((source()+m.OP,setter()),(source(),setter()+m.BYTE)):
            with self.assertRaisesRegex(ValueError,"drift"):m.patch(x,y)

if __name__=="__main__":
    unittest.main()
