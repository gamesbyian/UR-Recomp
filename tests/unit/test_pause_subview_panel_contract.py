import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


class PauseSubviewPanelContractTests(unittest.TestCase):
    def test_root_panel_is_not_drawn_behind_pause_subviews(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index("const bool pause_subview_panel = is_paused &&")
        guard = source[start:source.index("snes_ovl_fill_rect(", start)]
        for subview in ("g_options_visible", "g_controls_visible",
                        "g_quit_confirm_visible", "g_run_data_visible"):
            self.assertIn(subview, guard)
        self.assertIn("if (!frontend_options && !pause_subview_panel) {", guard)
        # The guard precedes every subview's own panel.
        self.assertLess(start, source.index('"QUIT TO DESKTOP?"', start))
        # The independent root quit dialog is never admitted while paused.
        self.assertIn("!paused()", source.split("bool modern_root_visible()", 1)[1].split("\n}", 1)[0])


if __name__ == "__main__":
    unittest.main()
