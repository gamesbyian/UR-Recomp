"""RF080 exact source-only isolated RF047 log stream hard failure tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import qa01_rf080_rf047_strict_source_sidecar as m

def fixture():
    return ('#include <stdbool.h>\n'
      '/* UR_QA01_RF047_NATIVE_NMI_RETURN_SOURCE_PIN */\n'
      '/* UR_QA01_RF076_FINITE_RECORDER_CAP_131072 */\n'
      '/* UR_QA01_RF079_NATIVE_POST_BIT_BRANCH */\n'
      'static void ur_rf047_emit(const char *fmt, ...) {\n'
      '  char line[512];\n'
      '  (void)write(2, line, (size_t)n);\n'
      '}\n'
      'void other(void) {ur_rf047_emit("event");}\n')

class SourceSidecar(unittest.TestCase):
    def test_original_stderr_writer_preserved_and_sidecar_is_additional(self):
        source=fixture()
        out=m.patch(source)
        self.assertEqual(out.count(m.STAMP),1)
        self.assertEqual(out.count('write(2, line, (size_t)n);'),1)
        self.assertEqual(out.count('ur_rf047_emit('),source.count('ur_rf047_emit('))
        self.assertIn('open(path,O_CREAT|O_TRUNC|O_WRONLY|O_CLOEXEC,0600)',out)
        self.assertIn('QA01RF080_SIDECAR_OPEN_FAILED',out)
        self.assertIn('QA01RF080_SIDECAR_WRITE_FAILED',out)
        self.assertLess(out.index('ur_rf080_source_event_write(line,(size_t)n);'),
                        out.index('write(2, line, (size_t)n);'))
        for bad in ('cpu_read8(', 'cpu_read16(', 'cpu_write8(', 'cpu_write16('):
            self.assertNotIn(bad,m.PATCH)

    def test_prerequisite_missing_or_ambiguous_writer_rejected(self):
        src=fixture()
        for bad in (
            src.replace('UR_QA01_RF079_NATIVE_POST_BIT_BRANCH','other'),
            src.replace('UR_QA01_RF047_NATIVE_NMI_RETURN_SOURCE_PIN','other'),
            src.replace('UR_QA01_RF076_FINITE_RECORDER_CAP_131072','other'),
            src.replace('write(2, line, (size_t)n);','write(1,line,n);'),
            src.replace('static void ur_rf047_emit','static void renamed'),
            src.replace('  (void)write(2, line, (size_t)n);',
                        '  (void)write(2, line, (size_t)n);\n  (void)write(2, line, (size_t)n);'),
        ):
            with self.subTest(bad=bad[:120]),self.assertRaises(ValueError):
                m.patch(bad)

    def test_double_staging_is_failure(self):
        with self.assertRaisesRegex(ValueError,'already or partially staged'):
            m.patch(m.patch(fixture()))

if __name__=='__main__':unittest.main()
