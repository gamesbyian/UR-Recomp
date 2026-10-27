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
    return (m.BYTE+"  actually_map(Byte,Address);\n}\n"+
            m.WORD+"  actually_write_word(Word,Address);\n}\n")

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
        self.assertLess(b.index("rf083_setword_entry(Word,Address,(int)w,(int)o);"),
                        b.index("actually_write_word(Word,Address);"))
        for marker in ("setter_entry","opcode_delta","QA01RF083ORIG_HEART",
                       "QA01RF083ORIG_TRUNCATED","clock=original_cpu",
                       "setterAddr=%06X","pc=%06X","6069u","6079u",
                       "QA01RF083ORIG_WORD_TRUNCATED","rawBefore=%04X"):
            self.assertIn(marker,a)
        for fn in ("S9xGetByte(","S9xGetWord(","S9xSetByte(","S9xSetWord("):
            self.assertNotIn(fn,m.C)

    def test_exact_repository_original_snes9x_source_layout(self):
        # Exercise the actual tracked reference-source snapshot, not only a
        # hand-authored 5-line fixture. Never alter the tracked source.
        root=Path(__file__).resolve().parents[2]/"third_party"/"src"/"snes9x-libretro"
        original=(root/"cpuexec.cpp").read_text(encoding="utf-8")
        getset=(root/"getset.h").read_text(encoding="utf-8")
        edited_cpu,edited_getset=m.patch(original,getset)
        self.assertEqual(edited_cpu.count("(*Opcodes[Op].S9xOpcode)();"),
                         original.count("(*Opcodes[Op].S9xOpcode)();"))
        self.assertEqual(edited_getset.count(m.BYTE),getset.count(m.BYTE))
        self.assertEqual(edited_getset.count(m.WORD),getset.count(m.WORD))
        self.assertIn("rf083_setbyte_entry(Byte,Address);",edited_getset)
        self.assertIn("rf083_setword_entry(Word,Address,(int)w,(int)o);",edited_getset)
        self.assertIn("rf083_post();",edited_cpu)

    def test_real_original_inc16_callsite_has_no_new_bus_operations(self):
        # This is the actual tracked pinned Snes9x macro, not a fake writer.
        root = Path(__file__).resolve().parents[2] / "third_party" / "src" / "snes9x-libretro"
        original = (root / "cpumacro.h").read_text(encoding="utf-8")
        patched = m.patch_macro(original)
        self.assertEqual(patched.count("S9xGetWord(OpAddress, w) + 1;"),
                         original.count("S9xGetWord(OpAddress, w) + 1;"))
        self.assertEqual(patched.count("S9xSetWord(Work16, OpAddress, w, WRITE_10);"),
                         original.count("S9xSetWord(Work16, OpAddress, w, WRITE_10);"))
        self.assertLess(patched.index("rf083_inc16_watch(OpAddress)"),
                        patched.index("S9xSetWord(Work16, OpAddress, w, WRITE_10);"))
        self.assertLess(patched.index("S9xSetWord(Work16, OpAddress, w, WRITE_10);"),
                        patched.index("rf083_inc16_commit(OpAddress, Work16"))
        self.assertIn("QA01RF083ORIG_INC16_TRUNCATED", m.C)
        self.assertIn("rawAfter=%04X", m.C)
        with self.assertRaisesRegex(ValueError, "already staged"):
            m.patch_macro(patched)
        with self.assertRaisesRegex(ValueError, "drift"):
            m.patch_macro(original.replace("S9xSetWord(Work16, OpAddress, w, WRITE_10);",
                                           "wrong_guest_write(Work16);"))

    def test_source_drift_and_partial_patch_refused(self):
        a,b=m.patch(source(),setter())
        for x,y in ((a,b),(source()+m.STAMP,setter()),
                    (source(),setter()+"rf083_setbyte_entry"),
                    (source().replace(m.OP,"fake()"),setter()),
                    (source().replace("Op = CPU.PCBase[Registers.PCw];",""),setter()),
                    (source().replace("Op = S9xGetByte(Registers.PBPC);",""),setter()),
                    (source(),setter().replace(m.BYTE,"fake_setter()")),
                    (source(),setter().replace(m.WORD,"fake_word_setter()"))):
            with self.subTest(size=(len(x),len(y))):
                with self.assertRaises(ValueError):m.patch(x,y)

    def test_ambiguous_callsites_refused(self):
        for x,y in ((source()+m.OP,setter()),(source(),setter()+m.BYTE),
                    (source(),setter()+m.WORD)):
            with self.assertRaisesRegex(ValueError,"drift"):m.patch(x,y)

if __name__=="__main__":
    unittest.main()
