from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "ci_log_assert.py"


class CiLogAssertTests(unittest.TestCase):
    def run_tool(self, text: str, *args: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run.log"
            path.write_text(text, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(TOOL), str(path), *args],
                text=True,
                capture_output=True,
                check=False,
            )

    def test_fields_are_order_independent(self) -> None:
        result = self.run_tool(
            "UR_HOST_STATE LOADED widescreen=16x9 extra=new display_mode=fullscreen\n",
            "--event", "UR_HOST_STATE LOADED",
            "--field", "display_mode=fullscreen",
            "--field", "widescreen=16x9",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_event_name_is_prefix_exact(self) -> None:
        result = self.run_tool(
            "NOT_UR_HOST_STATE LOADED widescreen=16x9\n",
            "--event", "UR_HOST_STATE LOADED",
            "--field", "widescreen=16x9",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing event", result.stderr)

    def test_missing_field_reports_matching_event(self) -> None:
        result = self.run_tool(
            "UR_HOST_STATE LOADED widescreen=original display_mode=windowed\n",
            "--event", "UR_HOST_STATE LOADED",
            "--field", "widescreen=16x9",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no line contained all fields", result.stderr)
        self.assertIn("UR_HOST_STATE LOADED", result.stderr)

    def test_absent_event_contract(self) -> None:
        result = self.run_tool(
            "UR_HOST_STATE AUTHENTIC_INERT\n",
            "--event", "UR_HOST_STATE LOADED",
            "--absent",
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
