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
        self.assertIn("ppm_crop_sha", source)
        self.assertIn("regional-europe-title.ppm", source)
        self.assertIn("regional-na-title.ppm", source)
        self.assertIn("regional-authentic-title.ppm", source)
        self.assertIn("UR_REGIONAL_TITLE visible=unirally guest_state_unchanged=1", source)
        self.assertIn("TARGET_RGB_SHA=\"40405f18ff1b856f2afe9e5ddfac77bcbd71e5ac9357532ef311e9509f6695bb\"", source)
        self.assertIn("test \"$EUROPE_VISIBLE_SHA\" = \"$TARGET_RGB_SHA\"", source)
        self.assertIn("test \"$EUROPE_VISIBLE_SHA\" != \"$NA_VISIBLE_SHA\"", source)
        self.assertIn("test \"$AUTHENTIC_VISIBLE_SHA\" = \"$NA_VISIBLE_SHA\"", source)
        self.assertIn("UR_REGIONAL_VISIBLE_SHA europe=", source)
        self.assertIn("cmp \"$EUROPE_VISUAL_DUMPS/boot-300.$suffix\" \"$NA_VISUAL_DUMPS/boot-300.$suffix\"", source)
        self.assertIn(
            "UR_REGIONAL_RESULT="
            "pal_saved_unirally_visible_ntsc_saved_uniracers_visible_"
            "guest_state_equal_main_menu_inert_authentic_canonical",
            source,
        )


if __name__ == "__main__":
    unittest.main()
