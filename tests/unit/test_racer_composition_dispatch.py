"""Guard the numeric-zero workflow dispatch contract for original Mesen capture."""

from pathlib import Path
import re
import unittest


WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/racer-composition-mesen.yml"


class RacerCompositionDispatchTests(unittest.TestCase):
    def test_zero_is_forwarded_without_truthiness_fallback(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertRegex(source, r"(?m)^\s+advance_frames:\s*$")
        self.assertRegex(source, r"(?m)^\s+default:\s*1218\s*$")
        self.assertRegex(source, r"(?m)^\s+required:\s*true\s*$")
        arguments = re.findall(r'--advance-frames\s+"([^"\n]+)"', source)
        self.assertEqual(arguments, ["${{ inputs.advance_frames }}"])
        self.assertNotIn("inputs.advance_frames ||", source)


if __name__ == "__main__":
    unittest.main()
