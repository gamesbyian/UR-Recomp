"""Negative native acceptance markers must fail in actual Bash, not just text checks."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = {
    "modern-onboarding-practice-acceptance.yml": 12,
    "modern-shared-native-acceptance.yml": 1,
    "modern-race-restart-acceptance.yml": 2,
    "windows-native-smoke.yml": 4,
}
NEGATIVE = re.compile(
    r'^if grep -(?:Fq|q) "(?P<marker>[^\"]+)" '
    r'"\$(?P<variable>[A-Za-z_][A-Za-z0-9_]*)(?P<suffix>/[^\"]+)?"; then$'
)


@unittest.skipUnless(shutil.which("bash"), "native acceptance requires Bash")
class WorkflowNegativeDiagnosticTests(unittest.TestCase):
    def test_all_19_checks_fail_closed_in_real_bash(self):
        for name, count in WORKFLOWS.items():
            source = (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
            self.assertNotRegex(source, r"(?m)^\s*!\s+grep\s")
            lines = source.splitlines()
            candidates = [i for i, line in enumerate(lines)
                          if NEGATIVE.fullmatch(line.strip())
                          and i + 1 < len(lines)
                          and 'echo "::error::Forbidden acceptance diagnostic"'
                          in lines[i + 1]]
            self.assertEqual(len(candidates), count, name)
            for index in candidates:
                match = NEGATIVE.fullmatch(lines[index].strip())
                self.assertIsNotNone(match)
                snippet = textwrap.dedent("\n".join(lines[index:index + 7])) + "\n"
                self.assertIn('elif [ "$?" -ne 1 ]; then', snippet)
                self.assertIn('echo "::error::Forbidden acceptance diagnostic"', snippet)
                self.assertIn('echo "::error::Could not inspect acceptance diagnostic"', snippet)
                with self.subTest(workflow=name, line=index + 1):
                    with tempfile.TemporaryDirectory() as folder:
                        root = Path(folder)
                        variable = match["variable"]
                        suffix = match["suffix"] or ""
                        env = os.environ.copy()
                        env[variable] = str(root) if suffix else str(root / "output.log")
                        log = Path(env[variable] + suffix)
                        for state, content in (
                            ("clean", "UNRELATED RECORD\n"),
                            ("forbidden", match["marker"] + "\n"),
                            ("missing", None),
                        ):
                            log.unlink(missing_ok=True)
                            if content is not None:
                                log.parent.mkdir(parents=True, exist_ok=True)
                                log.write_text(content, encoding="utf-8")
                            process = subprocess.run(
                                ["bash", "-euo", "pipefail", "-c", snippet],
                                env=env, capture_output=True, text=True, timeout=10,
                                check=False,
                            )
                            with self.subTest(state=state):
                                if state == "clean":
                                    self.assertEqual(process.returncode, 0, process.stderr)
                                else:
                                    self.assertNotEqual(process.returncode, 0)
                                    self.assertIn("::error::", process.stderr)


if __name__ == "__main__":
    unittest.main()
