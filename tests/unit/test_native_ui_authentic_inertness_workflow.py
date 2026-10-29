"""Original/native UI acceptance must fail on forbidden Authentic-mode tokens.

This test extracts the actual Bash check from workflow source, then executes
its positive and negative paths. A standalone '! grep' under errexit can
silently succeed; the explicit check must remain a real failing assertion.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/native-ui-evidence.yml"
FORBIDDEN = (
    "UR_HOST_STATE LOADED",
    "UR_DISPLAY_MODE APPLIED",
    "UR_VSYNC APPLIED",
    "UR_PRESENTATION_FPS APPLIED",
    "UR_OUTPUT_RESOLUTION",
    "UR_WIDESCREEN",
)


class NativeUiAuthenticInertnessWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        section = cls.source.split(
            "      - name: Modern settings persistence acceptance", 1,
        )[1].split("      - name:", 1)[0]
        start = section.index("          for marker in " + chr(92))
        end = section.index("          done", start) + len("          done")
        cls.check = textwrap.dedent(section[start:end]) + "\n"

    def run_real_check(self, content):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "authentic.log"
            path.write_text(content, encoding="utf-8")
            env = {**os.environ, "AUTH_LOG": str(path)}
            return subprocess.run(
                ["bash", "-e", "-o", "pipefail", "-c", self.check],
                env=env, capture_output=True, text=True, timeout=5,
                check=False,
            )

    def test_clean_authentic_log_passes(self):
        process = self.run_real_check("UR_HOST_STATE AUTHENTIC_INERT\n")
        self.assertEqual(process.returncode, 0, process.stderr)

    def test_each_forbidden_modern_token_rejects_real_bash_execution(self):
        for marker in FORBIDDEN:
            with self.subTest(marker=marker):
                process = self.run_real_check("UR_HOST_STATE AUTHENTIC_INERT\n" + marker + "\n")
                self.assertNotEqual(process.returncode, 0)
                self.assertIn(marker, process.stderr)

    def test_workflow_retains_authentic_and_original_candidate_gates(self):
        self.assertNotIn("          ! grep -q ", self.source)
        self.assertIn('if grep -q "$marker" "$AUTH_LOG"; then', self.source)
        for marker in FORBIDDEN:
            self.assertIn('"' + marker + '"', self.check)
        self.assertIn('grep -q "UR_HOST_STATE AUTHENTIC_INERT" "$AUTH_LOG"', self.source)
        self.assertIn("name: modern-native-canonical-candidate", self.source)
        self.assertIn("Upload bridged native UI candidate", self.source)
        self.assertIn("shard: [core, navigation, results-a, results-b, records, profiles]", self.source)
        self.assertIn("needs.build.result == 'success' && needs.capture.result == 'success'", self.source)

    def test_dump_assertions_preserve_fail_closed_missing_file(self):
        self.assertIn('test -f "$script"', self.source)
        self.assertIn("while IFS= read -r tag; do", self.source)
        self.assertIn("done < <(awk", self.source)
        self.assertIn('exit "$missing"', self.source)


if __name__ == "__main__":
    unittest.main()
