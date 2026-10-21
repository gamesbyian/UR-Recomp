"""The NTFS evidence predicates must remain active with python -O."""
import subprocess
import sys
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "tools" / "qa02_independent_ntfs_artifact_check.py"

class OptimizedEvidenceChecks(unittest.TestCase):
    def test_all_source_conditions_remain_live_under_optimized_python(self):
        script = ("import importlib.util\n"
                  "s=importlib.util.spec_from_file_location('audit', %r)\n"
                  "m=importlib.util.module_from_spec(s)\n"
                  "s.loader.exec_module(m)\n"
                  "try:\n"
                  " m.require(False, 'forced refusal')\n"
                  "except AssertionError:\n"
                  " print('refused')\n"
                  "else:\n"
                  " raise SystemExit('optimized-away evidence predicate')\n") % str(TOOL)
        for option in ([], ["-O"], ["-OO"]):
            with self.subTest(option=option):
                result = subprocess.run([sys.executable,*option,"-c",script],
                                        capture_output=True,text=True,timeout=15)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertIn("refused",result.stdout)

    def test_tool_retains_no_source_assert_statements(self):
        import ast
        parsed=ast.parse(TOOL.read_text(encoding="utf-8"))
        self.assertFalse(any(isinstance(node,ast.Assert) for node in ast.walk(parsed)))

if __name__=="__main__":
    unittest.main()
