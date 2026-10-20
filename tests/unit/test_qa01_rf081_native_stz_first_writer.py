"""RF081 native source-only real paced STZ commit and RF047 ordinal tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf081_native_stz_first_writer as m
import qa01_rf079_native_real_bit_branch as rf079
import qa01_rf080_rf047_strict_source_sidecar as rf080

def beam():
    return ('/* '+rf079.STAMP+' */\n'
            '/* '+rf080.STAMP+' */\n'
            'static int ur_rf079_enabled(void) {return 1;}\n'
            'static int ur_rf047_allow_row(void) {return 1;}\n'
            'static unsigned long long ur_rf047_seq;\n'
            'static void ur_rf047_emit(const char *s, ...);\n'
            'void ur_rf047_mark_executed_pc(uint32_t pc, unsigned tier) {\n'
            '    emit_opcode(pc);\n'
            '}\n')
def cpu():
    return ('uint8_t cpu_read8_paced(CpuState *cpu, uint8_t bank, uint16_t addr) {\n'
            '    const uint8_t ur_rf079_actual_value=cpu_read8(cpu, bank, addr);\n'
            '    ur_rf079_native_actual_bit_read(cpu,bank,addr,ur_rf079_actual_value);\n'
            '    return ur_rf079_actual_value;\n'
            '}\n'
            'void cpu_write8_paced(CpuState *cpu, uint8_t bank, uint16_t addr, uint8_t v) {\n'
            '    cpu->master_cycles += cpu_region_speed(addr);\n'
            '    cpu_write8(cpu, bank, addr, v);\n'
            '}\n\nvoid cpu_write16_paced(CpuState *cpu, uint8_t bank, uint16_t addr, uint16_t v) {\n'
            '}\n')

class NativeStzWriter(unittest.TestCase):
    def test_real_paced_byte_write_and_postcommit_value(self):
        old_b,old_c=beam(),cpu()
        b,c=m.patch(old_b,old_c)
        self.assertEqual(b.count(m.STAMP),1)
        self.assertEqual(b.count(m.RECORDER),1)
        self.assertEqual(c.count('cpu_write8(cpu, bank, addr, v);'),1)
        self.assertEqual(c.count('cpu_read8('),old_c.count('cpu_read8('))
        self.assertIn('ur_rf081_native_opcode(pc,tier);',b)
        self.assertIn('stage=stz_real_commit',b)
        self.assertIn('QA01RF081NATIVE_STZ_MISSING_WRITE',b)
        self.assertLess(c.index('cpu_write8(cpu, bank, addr, v);'),
                        c.index('ur_rf081_native_committed_stz(cpu,bank,addr,v);'))
        self.assertIn('cpu->ram[addr]',b)
        self.assertIn('master=%llu',b)

    def test_missing_native_prerequisites_or_paced_callsite_rejected(self):
        x,y=beam(),cpu()
        for a,b in (
            (x.replace(rf079.STAMP,'missing'),y),
            (x.replace(rf080.STAMP,'missing'),y),
            (x.replace(m.RECORDER,'other'),y),
            (x,y.replace('ur_rf079_native_actual_bit_read(cpu,bank,addr,ur_rf079_actual_value);','gone;')),
            (x,y.replace('cpu_write8(cpu, bank, addr, v);','write_guest();')),
        ):
            with self.assertRaises(ValueError):
                m.patch(a,b)

    def test_double_staging_fails(self):
        a,b=m.patch(beam(),cpu())
        with self.assertRaisesRegex(ValueError,'already or partly staged'):
            m.patch(a,b)

if __name__=="__main__":
    unittest.main()
