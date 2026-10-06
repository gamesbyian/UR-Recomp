import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tests" / "native" / "run_modern_tour_entry_acceptance.sh"


class ModernTourAcceptanceHarnessTests(unittest.TestCase):
    def test_shell_syntax_and_single_canonical_tail(self):
        subprocess.run(["bash", "-n", str(HARNESS)], cwd=ROOT, check=True)

        source = HARNESS.read_text(encoding="utf-8")
        self.assertEqual(
            source.count("run_ui_case restart-confirm-cancel restart-confirm-cancel"),
            1,
        )
        self.assertEqual(
            source.count("run_ui_case restart-persist-fail restart-persist-fail"),
            1,
        )
        self.assertEqual(
            source.count("# Stale source mismatch must fail closed before routing."),
            1,
        )
        self.assertEqual(
            source.count("# Authentic mode must never expose or route Modern continuation."),
            1,
        )
        self.assertEqual(
            source.count("UR_TOUR_ENTRY_ACCEPTANCE_RESULT="),
            1,
        )
        self.assertIn(
            "grep -q '^tour_resume=0:0:0:11000$' "
            '"$RESTART_FAIL_ROOT/host-profile.txt"',
            source,
        )


if __name__ == "__main__":
    unittest.main()
