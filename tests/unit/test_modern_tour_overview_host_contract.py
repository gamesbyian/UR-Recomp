import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native/product/uniracers_modern_host.cpp"
TITLE = ROOT / "native/title/uniracers_tour_progress_overview.hpp"
HARNESS = ROOT / "tests/native/run_modern_tour_overview_acceptance.sh"


class ModernTourOverviewHostContractTests(unittest.TestCase):
    def test_shortcuts_use_keyboard_and_mapped_p1_semantics(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn("key == SDLK_F7", source)
        self.assertIn("pressed && control == 10 && modern_mode()", source)
        self.assertIn("open_progress_overview()", source)
        self.assertIn("g_progress_overview_visible", source)
        self.assertIn("close_progress_overview(\"UR_TOUR_OVERVIEW CLOSED\")", source)
        raw = source.split(
            'extern "C" int ur_uniracers_modern_system_gamepad_button(', 1
        )[1].split(
            'extern "C" int ur_uniracers_modern_system_gamepad_control(', 1
        )[0]
        self.assertNotIn("kGamepadBtn_L1", raw)
        self.assertIn(
            "g_progress_overview_visible ||\n            practice_routing()",
            source,
        )

    def test_progression_model_only_reads_stock_source(self):
        title = TITLE.read_text(encoding="utf-8")
        self.assertIn("stock_practice_tour_option_mask(", title)
        self.assertIn("kMedalBase = 0x069C", title)
        self.assertIn("tour_option < 8", title)
        self.assertNotIn("sram[", title.replace("sram[kMedalBase +", ""))
        self.assertNotIn("memcpy(", title)
        self.assertNotIn("RtlTryWriteSram(", title)

    def test_real_native_acceptance_is_wired(self):
        subprocess.run(["bash", "-n", str(HARNESS)], cwd=ROOT, check=True)
        workflow = (
            ROOT / ".github/workflows/modern-onboarding-practice-acceptance.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "run_case tour-overview run_modern_tour_overview_acceptance.sh",
            workflow,
        )
        self.assertIn(
            "UR_TOUR_OVERVIEW PRESENT scale=", HARNESS.read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    unittest.main()
