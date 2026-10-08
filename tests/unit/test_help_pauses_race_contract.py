import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


class HelpPausesRaceContractTests(unittest.TestCase):
    def test_f1_pauses_a_running_race_before_help_opens(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index("key == SDLK_F1 && !host_subview_visible()")
        body = source[start:source.index('"UR_ONBOARDING HELP_OPENED"', start)]
        self.assertIn("!paused() && g_ram && g_ram[0x0313] == 0x01", body)
        self.assertIn("dispatch(UR_MODERN_PAUSE_TOGGLE)", body)
        self.assertIn("HELP_REFUSED_RUNNING_RACE", body)
        self.assertLess(body.index("dispatch(UR_MODERN_PAUSE_TOGGLE)"),
                        body.index("g_onboarding_visible = true;"))

    def test_paused_footer_hint_yields_to_help(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index('extern "C" int ur_uniracers_modern_subview_active(void) {')
        body = source[start:source.index("}\n", start)]
        self.assertIn("onboarding_surface_active()", body)


if __name__ == "__main__":
    unittest.main()
