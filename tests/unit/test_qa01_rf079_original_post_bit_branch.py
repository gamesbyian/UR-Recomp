"""RF079 original source-only true BIT/BPL post-op probe adversarial guards."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import qa01_rf076_original_opcode_fetch_source as rf076
import qa01_rf079_original_post_bit_branch as m

def fixture():
    return (rf076.HEADER + '\n' + rf076.HOOK +
        'void S9xMainLoop (void) {\n'
        '\t\t\tur_rf076_original_fetched_opcode("fetch", Op);\n'
        '\t\t\tRegisters.PCw++;\n'
        '\t\t\t(*Opcodes[Op].S9xOpcode)();\n'
        '}\n')

class OriginalBitBranch(unittest.TestCase):
    def test_original_post_dispatch_keeps_real_guest_operations_once(self):
        src=fixture()
        out=m.patch(src)
        self.assertEqual(out.count(m.STAMP),1)
        self.assertEqual(out.count('(*Opcodes[Op].S9xOpcode)();'),1)
        self.assertEqual(out.count('Registers.PCw++;'),1)
        self.assertIn('ICPU._Negative',out)
        self.assertIn('QA01RF079ORIG_TRUNCATED',out)
        self.assertIn('phase=after_real_guest_opcode',out)
        self.assertLess(out.index('(*Opcodes[Op].S9xOpcode)();'),
                        out.index('ur_rf079_original_post_op(ur_rf079_prepc,Op);'))
        self.assertEqual(out.count('S9xGetByte('),src.count('S9xGetByte('))
    def test_unstaged_or_duplicate_dispatch_rejected(self):
        src=fixture()
        for bad in (src.replace(rf076.STAMP,'other'),
                    src.replace(rf076.HOOK,''),
                    src.replace('(*Opcodes[Op].S9xOpcode)();','broken();'),
                    src.replace(m.OLD,m.OLD+'\n'+m.OLD)):
            with self.subTest(bad=bad[:50]),self.assertRaises(ValueError):
                m.patch(bad)
    def test_second_staging_rejected(self):
        with self.assertRaisesRegex(ValueError,'already/partially staged'):
            m.patch(m.patch(fixture()))

if __name__=='__main__':unittest.main()
