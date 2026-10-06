import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tests" / "native" / "run_modern_regional_secret_acceptance.sh"


class RegionalPresentationNativeAcceptanceContractTests(unittest.TestCase):
    def test_shell_syntax(self):
        subprocess.run(["bash", "-n", str(SCRIPT)], cwd=ROOT, check=True)

    def test_acceptance_covers_live_persistence_and_negative_surfaces(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('run_secret_process "p a l" "europe"', source)
        self.assertIn(
            'run_secret_process "n t s c" "north_america" "europe"',
            source,
        )
        self.assertIn("regional-main-menu-ready.wram.bin", source)
        self.assertIn("UR_EXECUTION_MODE=authentic", source)
        self.assertIn("UR_HOST_STATE AUTHENTIC_INERT", source)
        self.assertIn(
            "UR_REGIONAL_RESULT="
            "pal_saved_reloaded_ntsc_saved_reloaded_"
            "main_menu_inert_authentic_inert",
            source,
        )


if __name__ == "__main__":
    unittest.main()
