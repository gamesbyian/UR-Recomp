"""RF081 exact 2014 original STZ setbyte source and postdispatch tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf081_original_stz_first_writer as m
import qa01_rf079_original_post_bit_branch as rf079

def executor():
    return ('#include "movie.h"\n'
            '/* '+rf079.STAMP+' */\n'
            'void S9xMainLoop(void) {\n'
            '\t\t\tconst unsigned ur_rf079_prepc = 0;\n'
            '\t\t\tRegisters.PCw++;\n'
            '\t\t\t(*Opcodes[Op].S9xOpcode)();\n'
            '\t\t\tur_rf079_original_post_op(ur_rf079_prepc,Op);\n'
            '}\n')
def getset():
    return ('/* UR_QA01_RF063_SOURCE_BUS_CHECKPOINT_SEQUENCE */\n'
            'inline void S9xSetByte (uint8 Byte, uint32 Address)\n'
            '{\n'
            '    int block = 1;\n'
            '    *(Memory.RAM + (Address & 0xffff)) = Byte;\n'
            '}\n')

class OriginalStzWriter(unittest.TestCase):
    def test_real_setter_and_actual_postdispatch_mirror(self):
        e,g=executor(),getset()
        x,y=m.patch(e,g)
        self.assertEqual(x.count(m.STAMP),1)
        self.assertEqual(x.count('(*Opcodes[Op].S9xOpcode)();'),1)
        self.assertEqual(x.count('Registers.PCw++;'),1)
        self.assertEqual(x.count('ur_rf081_original_after_dispatch(ur_rf079_prepc,Op);'),1)
        self.assertLess(x.index("(*Opcodes[Op].S9xOpcode)();"),
                        x.index("ur_rf081_original_after_dispatch(ur_rf079_prepc,Op);"))
        self.assertIn('ur_rf081_original_actual_setbyte(Byte,Address);',y)
        self.assertIn('QA01RF081ORIG_TRUNCATED',x)
        self.assertIn('Memory.RAM[addr]',x)
        for op in ('S9xGetByte(','S9xGetWord(','S9xSetByte(','S9xSetWord('):
            self.assertEqual(x.count(op)+y.count(op),e.count(op)+g.count(op))

    def test_unstaged_or_ambiguous_original_source_fails(self):
        e,g=executor(),getset()
        for xe,xg in (
            (e.replace(rf079.STAMP,'other'),g),
            (e,g.replace('UR_QA01_RF063_SOURCE_BUS_CHECKPOINT_SEQUENCE','other')),
            (e.replace('(*Opcodes[Op].S9xOpcode)();','run_guest();'),g),
            (e,g.replace('inline void S9xSetByte (uint8 Byte, uint32 Address)','broken')),
            (e.replace('\t\t\tur_rf079_original_post_op(ur_rf079_prepc,Op);\n',''),g),
        ):
            with self.subTest(case=xe[:65]),self.assertRaises(ValueError):
                m.patch(xe,xg)

    def test_already_staged_fails_closed(self):
        a,b=m.patch(executor(),getset())
        with self.assertRaisesRegex(ValueError,'already or partly staged'):
            m.patch(a,b)

if __name__=="__main__":
    unittest.main()
