"""RF084 true generated native paced-word and paced-byte writer controls."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf084_native_sound_dp_committed_writer as m

def fixture():
    return (m.HEADER+
        m.COUNTER+"\n"+m.COUNTER_LABEL+
        "  {\n    uint8 _im = 42;\n"+m.COUNTER_WRITE+"  }\n}\n"+
        m.POINTER+"\n"+m.POINTER_LABEL+
        "  {\n    uint16 _im = 42;\n"+m.POINTER_WRITE+"  }\n}\n"+
        "RecompReturn NextFunc(CpuState *cpu) {\n  return 0;\n}\n")

class RF084GeneratedWrite(unittest.TestCase):
    def test_real_paced_write8_and_write16_after_return(self):
        patched=m.patch(fixture())
        self.assertEqual(patched.count(m.STAMP),1)
        self.assertEqual(patched.count(m.COUNTER_WRITE),1)
        self.assertEqual(patched.count(m.POINTER_WRITE),1)
        self.assertLess(patched.index(m.COUNTER_WRITE),
                        patched.index("ur_rf084_after(cpu,0x8280E0"))
        self.assertLess(patched.index(m.POINTER_WRITE),
                        patched.index("ur_rf084_after(cpu,0x828154"))
        self.assertIn("native_master=%llu",patched)
        self.assertIn("QA01RF084NATIVE_TRUNCATED",patched)
        self.assertIn("variant=M1X0",patched)
        self.assertIn("rawAfter=%04X",patched)
        self.assertIn('getenv("UR_QA01_RF084_NATIVE_SOUND_DP")',patched)
        for bus in ("cpu_read8(", "cpu_read16(", "cpu_write8(", "cpu_write16("):
            self.assertNotIn(bus,m.HOOK)

    def test_observer_requires_exact_one_opt_in(self):
        # Compile the exact C predicate emitted into generated native source.
        # An explicit "0" must never silently turn on instrumentation.
        self.assertIn("if(!ur_rf084_opt_in(flag) ||", m.HOOK)
        compiler = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
        if not compiler:
            self.skipTest("no C compiler available for generated predicate")
        helper = ("static int ur_rf084_opt_in" +
                  m.HOOK.split("static int ur_rf084_opt_in", 1)[1]
                  .split("static void ur_rf084_after", 1)[0])
        source = "#include <stddef.h>\n" + helper + """
int main(void) {
    const char *flags[] = {"", "0", "1", "10", "true", "01"};
    const int expected[] = {0, 0, 1, 0, 0, 0};
    if (ur_rf084_opt_in(NULL)) return 1;
    for (int i = 0; i < 6; ++i)
        if (ur_rf084_opt_in(flags[i]) != expected[i]) return i + 2;
    return 0;
}
"""
        with tempfile.TemporaryDirectory() as temp:
            c_file = Path(temp) / "rf084_opt_in.c"
            executable = Path(temp) / "rf084_opt_in"
            c_file.write_text(source, encoding="utf-8")
            subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra",
                            "-Werror", str(c_file), "-o", str(executable)],
                           check=True, capture_output=True, text=True)
            subprocess.run([str(executable)], check=True,
                           capture_output=True, text=True)

    def test_existing_native_source_callsite_drift_refused(self):
        source=fixture()
        for mutated in (source.replace(m.COUNTER_WRITE,""),
                        source.replace(m.POINTER_WRITE,""),
                        source.replace(m.COUNTER_LABEL,""),
                        source.replace(m.POINTER_LABEL,""),
                        source.replace(m.HEADER,""),
                        source+m.COUNTER,
                        source.replace(m.POINTER,
                          "RecompReturn WrongMode_M0X0(CpuState *cpu) {")):
            with self.subTest(case=len(mutated)),self.assertRaises(ValueError):
                m.patch(mutated)

    def test_already_staged_native_source_refused(self):
        with self.assertRaisesRegex(ValueError,"already or partly"):
            m.patch(m.patch(fixture()))

if __name__=="__main__":unittest.main()
