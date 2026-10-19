"""2014 original opcode fetch marks existing byte after actual direct/slow fetch."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import qa01_rf076_original_opcode_fetch_source as m


def fixture():
    return ('static inline void S9xReschedule (void);\n'
            'void S9xMainLoop (void) {\n'
            '\t\t\t\tTimings.NMITriggerPos = 0xffff;\n'
            '\t\t\t\tif (CPU.WaitingForInterrupt)\n'
            '\t\t\t\tS9xOpcode_NMI();\n'
            '\t\t\t\tOp = CPU.PCBase[Registers.PCw];\n'
            '\t\t\t\tOp = S9xGetByte(Registers.PBPC);\n'
            '\t\t\tRegisters.PCw++;\n'
            '\t\t\t(*Opcodes[Op].S9xOpcode)();\n}\n')


class OriginalFetch(unittest.TestCase):
    def test_true_pre_increment_opcode_marker_and_real_nmi(self):
        old = fixture()
        src = m.patch(old)
        self.assertEqual(src.count(m.STAMP), 2)
        self.assertLess(src.index('ur_rf076_original_fetched_opcode("fetch", Op);'),
                        src.index('Registers.PCw++;'))
        self.assertLess(src.index('ur_rf076_original_fetched_opcode("nmi_pending", 0);'),
                        src.index('if (CPU.WaitingForInterrupt)'))
        self.assertLess(src.index('ur_rf076_original_fetched_opcode("nmi_pending", 0);'),
                        src.index('ur_rf076_original_fetched_opcode("nmi_before", 0);'))
        self.assertLess(src.index('ur_rf076_original_fetched_opcode("nmi_before", 0);'),
                        src.index('S9xOpcode_NMI();'))
        self.assertLess(src.index('Op = CPU.PCBase[Registers.PCw];'),
                        src.index('ur_rf076_original_fetched_opcode("fetch", Op);'))
        self.assertLess(src.index('Op = S9xGetByte(Registers.PBPC);'),
                        src.index('ur_rf076_original_fetched_opcode("fetch", Op);'))
        self.assertIn('actualFetchedPC=%06X fetchedOpcode=%02X', src)
        self.assertIn('wai=%u', src)
        self.assertIn('UR_QA01_RF076_ORIGINAL_FETCH_PC', src)
        self.assertIn('QA01RF076ORIGPC_TRUNCATED', src)
        self.assertEqual(old.count('S9xGetByte('), src.count('S9xGetByte('))
        self.assertEqual(old.count('S9xOpcode_NMI();'), src.count('S9xOpcode_NMI();'))
        self.assertEqual(old.count('Registers.PCw++;'), src.count('Registers.PCw++;'))

    def test_missing_fast_or_slow_fetch_fails(self):
        for a in ('Op = CPU.PCBase[Registers.PCw];',
                  'Op = S9xGetByte(Registers.PBPC);'):
            with self.subTest(a=a), self.assertRaises(ValueError):
                m.patch(fixture().replace(a, 'BAD;'))

    def test_ambiguous_guest_dispatch_or_nmi_fails(self):
        for a in (m.HEADER, m.FETCH, m.NMI, m.NMI_WAKE):
            with self.subTest(a=a), self.assertRaises(ValueError):
                m.patch(fixture().replace(a, a+a))

    def test_no_duplicate_source_staging(self):
        with self.assertRaisesRegex(ValueError, 'already staged'):
            m.patch(m.patch(fixture()))


if __name__ == '__main__':
    unittest.main()
