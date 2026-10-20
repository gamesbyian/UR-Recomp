"""RF079 native source-only true returned-byte and N flag probe guards."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import qa01_rf079_native_real_bit_branch as m

def beam():
    return (
        '/* UR_QA01_RF047_EXECUTED_GUEST_OPCODE_PC */\n'
        '/* UR_QA01_RF076_FINITE_RECORDER_CAP_131072 */\n'
        'void ur_rf047_mark_executed_pc(uint32_t pc, unsigned tier) {\n'
        '  if (ur_rf047_allowed()) {\n'
        '    if (!ur_rf047_allow_row()) return;\n'
        '    ur_rf047_emit("QA01RF047NATIVE seq=%llu");\n'
        '    return;\n'
        '  }\n'
        "  /* RF047's NMI coverage stays restricted */\n"
        '}\n')
def cpu():
    return ('uint8_t cpu_read8_paced(CpuState *cpu, uint8_t bank, uint16_t addr) {\n'
            '    cpu->master_cycles += cpu_region_speed(0);\n'
            '    return cpu_read8(cpu, bank, addr);\n'
            '}\n\nuint16_t cpu_read16_paced(CpuState *cpu, uint8_t bank, uint16_t addr) {\n'
            '    return 0;\n'
            '}\n')
class NativeBitBranch(unittest.TestCase):
    def test_actual_return_replaces_but_never_duplicates_real_guest_read(self):
        orig_b,orig_c=beam(),cpu()
        b,c=m.patch(orig_b,orig_c)
        self.assertEqual(b.count(m.STAMP),1)
        self.assertEqual(c.count('cpu_read8(cpu, bank, addr)'),1)
        self.assertEqual(c.count('cpu_read8_paced('),1)
        self.assertEqual(c.count('ur_rf079_native_actual_bit_read('),2)
        self.assertIn('stage=bit_real_return',b)
        self.assertIn('stage=bpl_actual_input',b)
        self.assertIn('cpu->_flag_N',b) if 'cpu->_flag_N' in b else self.assertIn('g_cpu._flag_N',b)
        self.assertLess(c.index('const uint8_t ur_rf079_actual_value=cpu_read8'),
                        c.index('ur_rf079_native_actual_bit_read(cpu,bank,addr'))
        self.assertLess(c.index('ur_rf079_native_actual_bit_read(cpu,bank,addr'),
                        c.index('return ur_rf079_actual_value'))
        self.assertNotIn('cpu_read8(',b)
    def test_preflight_requires_real_rf047_and_exact_paced_read(self):
        for b,c in (
            (beam().replace('UR_QA01_RF047_EXECUTED_GUEST_OPCODE_PC','bogus'),cpu()),
            (beam().replace('UR_QA01_RF076_FINITE_RECORDER_CAP_131072','bogus'),cpu()),
            (beam().replace(m.RECORDER_END,'broken'),cpu()),
            (beam(),cpu().replace('return cpu_read8(cpu, bank, addr);','return 0;')),
        ):
            with self.assertRaises(ValueError):
                m.patch(b,c)
    def test_double_patch_fails_closed(self):
        b,c=m.patch(beam(),cpu())
        with self.assertRaisesRegex(ValueError,'already/partially staged'):
            m.patch(b,c)

if __name__=='__main__':unittest.main()
