"""Finite RF047 recorder widening, no guest bus calls or silent overflow."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools'))
import qa01_rf076_rf047_capacity_patch as m


def fixture():
    return ('/* UR_QA01_RF047_NATIVE_NMI_RETURN_SOURCE_PIN */\n'
            'const char truncated[] = "QA01RF047NATIVE_TRUNCATED\\n";\n'
            'int ur_rf047_allow_row(void) {\n'
            '  if (!ur_rf047_allowed()) return 0;\n'
            '  if (ur_rf047_events++ >= 8192u) {\n'
            '    if (ur_rf047_events == 8193u)\n'
            '      ur_rf047_emit("QA01RF047NATIVE_TRUNCATED\\n");\n'
            '    return 0;\n'
            '  }\n'
            '  return 1;\n'
            '}\n')


class Cap(unittest.TestCase):
    def test_finite_cap_and_explicit_overflow_survive(self):
        raw=fixture()
        updated=m.patch(raw)
        self.assertIn(m.NEW_LIMIT, updated)
        self.assertIn(m.NEW_OVERFLOW, updated)
        self.assertIn(m.TAG, updated)
        self.assertEqual(updated.count('QA01RF047NATIVE_TRUNCATED'),2)
        self.assertEqual(raw.count('ur_rf047_allowed()'),updated.count('ur_rf047_allowed()'))
        for s in ('cpu_read8(', 'cpu_read16(', 'S9xGetByte(', 'cpu_write8('):
            self.assertEqual(raw.count(s),updated.count(s))
        self.assertEqual(updated.count('return 0;'),raw.count('return 0;'))

    def test_missing_or_ambiguous_original_guard_fails(self):
        raw=fixture()
        for src in (raw.replace('8192u','8191u'),raw.replace('8193u','8192u'),
                    raw.replace('QA01RF047NATIVE_TRUNCATED','CHANGED'),
                    raw+raw):
            with self.subTest(src=src[:100]),self.assertRaises(ValueError): m.patch(src)

    def test_double_patch_and_truncated_reporter_removed_fail(self):
        src=m.patch(fixture())
        with self.assertRaises(ValueError):m.patch(src)
        with self.assertRaises(ValueError):
            m.patch(fixture().replace('ur_rf047_emit("QA01RF047NATIVE_TRUNCATED\\n");',
                                      'ur_rf047_emit("OTHER\\n");'))


if __name__=='__main__':
    unittest.main()
