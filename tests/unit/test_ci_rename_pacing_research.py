"""Temporary Rename editor five-branch pacing parity proof contract."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class RenamePacingExperimentTest(unittest.TestCase):
    def test_controls_are_isolated_and_authoritative_capture_preserved(self):
        w = (ROOT / ".github/workflows/native-ui-evidence.yml").read_text()
        profile = w.split("            profiles)", 1)[1].split("            *)", 1)[0]
        original = "run_route ui-rename-editor-explore ui-rename-editor-explore.script ui-rename-editor-dumps 180"
        self.assertEqual(w.count(original), 1)
        self.assertLess(profile.index(original), profile.index("for pacing in paced unpaced; do"))
        self.assertIn('export SNESRECOMP_USER_DATA_DIR="$RUNNER_TEMP/ui-rename-$pacing-user"', profile)
        self.assertIn('grep -Fq "config dir anchored: $SNESRECOMP_USER_DATA_DIR"', profile)
        self.assertIn('hashlib.sha256(p.read_bytes()).hexdigest()', profile)
        self.assertIn("if drift:", profile)
        self.assertIn("UR_RENAME_PACING_PARITY PASS", profile)
        self.assertIn("ui-rename-editor-explore:ui-rename-editor-dumps", w.split("  aggregate:", 1)[1])
        script = (ROOT / "tests/input/ui-rename-editor-explore.script").read_text()
        self.assertEqual(sum(x.lstrip().startswith("dump ") for x in script.splitlines()), 11)
        self.assertEqual(sum(x.strip() == "reset" for x in script.splitlines()), 4)


if __name__ == "__main__":
    unittest.main()
