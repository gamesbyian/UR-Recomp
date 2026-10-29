"""Execute actual Bash negative markers from source-owned research workflows.

Standalone '! grep -q ...' bypasses Bash errexit. These are evidence-integrity
checks, not evidence of original/native parity or a release gate.
"""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CASES = (
    ("qa-cumulative-native-metrics.yml", "not found", "native-metrics-ldd.txt"),
    ("qa08-original-2p-hdma-table-writers.yml", "UR_QA08_COLDATA_TABLE_WRITER_OVERFLOW", "original.log"),
    ("qa08-original-2p-hdma-table-writers.yml", "UR_QA08_INIDISP_TABLE_WRITER_OVERFLOW", "original.log"),
    ("qa08-original-hdma-writer-opcodes.yml", "UR_QA08_ORIGINAL_HDMA_OPCODE_OVERFLOW", "qa08-original-opcode.log"),
)


@unittest.skipUnless(shutil.which("bash"), "requires real Bash")
class ResearchNegativeMarkerGuards(unittest.TestCase):
    def test_actual_workflow_guards_reject_forbidden_and_unreadable_logs(self):
        sources = {}
        for name, marker, log_name in CASES:
            if name not in sources:
                source = (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
                self.assertNotRegex(source, r"(?m)^\s*!\s+grep\s", name)
                sources[name] = source
            lines = sources[name].splitlines()
            expected = "if grep -q '" + marker + "' "
            positions = [i for i, line in enumerate(lines)
                         if line.lstrip().startswith(expected)]
            self.assertEqual(len(positions), 1, (name, marker))
            first = positions[0]
            indent = len(lines[first]) - len(lines[first].lstrip())
            ends = [i for i in range(first + 1, len(lines))
                    if lines[i] == " " * indent + "fi"]
            self.assertTrue(ends, (name, marker))
            guard = "\n".join(line[indent:] for line in lines[first:ends[0] + 1])
            self.assertIn("grep_rc=$?", guard)
            self.assertIn('if [ "$grep_rc" -ne 1 ]; then', guard)
            self.assertIn("exit 1", guard)
            script = "set -euo pipefail\n" + guard + "\nprintf 'GUARD_OK\\n'\n"

            for mode in ("clean", "forbidden", "missing"):
                with self.subTest(workflow=name, marker=marker, mode=mode):
                    with tempfile.TemporaryDirectory() as temp:
                        log = Path(temp, log_name)
                        if mode != "missing":
                            log.write_text(
                                ("healthy dependencies\n" if mode == "clean"
                                 else "diagnostic: " + marker + "\n"),
                                encoding="utf-8",
                            )
                        env = dict(os.environ, RUNNER_TEMP=temp, stem=temp)
                        result = subprocess.run(
                            ["bash", "-c", script], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=10,
                            check=False,
                        )
                        if mode == "clean":
                            self.assertEqual(result.returncode, 0, result.stderr)
                            self.assertIn("GUARD_OK", result.stdout)
                        else:
                            self.assertNotEqual(result.returncode, 0, result.stdout)
                            self.assertIn("::error::", result.stderr)
                            self.assertNotIn("GUARD_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
