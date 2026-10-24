"""ROM-free source contracts for Records/Local Runs presentation density.

The Modern overlay compositor is separately compiled and exercised by
test_modern_overlay_composition_cpp.py and the resize matrix. These guards
ensure the two Records host painters consume that same authoritative scale.
"""
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
RECORDS_HOST = ROOT / "native" / "product" / "completed_run_browser_host.cpp"
MODERN_HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


def function_body(source, start, end):
    return source.split(start, 1)[1].split(end, 1)[0]


class CompletedRunOverlayDensityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = RECORDS_HOST.read_text(encoding="utf-8")
        cls.modern = MODERN_HOST.read_text(encoding="utf-8")

    def assert_scaled_browser(self, start, end):
        body = function_body(self.records, start, end)
        self.assertIn("resolve_modern_overlay_surface_scale(", body)
        self.assertIn("ur_uniracers_modern_presentation_scale()", body)
        self.assertIn("const int logical_width = width / scale;", body)
        self.assertIn("const int logical_height = height / scale;", body)
        self.assertIn("logical_width < 244 ? logical_width - 12 : 236", body)
        self.assertIn("panel_h > logical_height", body)
        self.assertIn("(logical_width - panel_w) / 2", body)
        self.assertIn("(logical_height - panel_h) / 2", body)
        self.assertIn("panel_w * scale, panel_h * scale", body)
        self.assertIn("(x + 8) * scale, line_y * scale", body)
        self.assertIn("fitted.c_str(), 0xFFFFFFFFu, scale", body)
        self.assertNotIn("pixels, stride, height, x + 8, line_y", body)
        self.assertNotIn("pixels, stride, height, x, y, panel_w, panel_h", body)

    def test_records_panel_scales_all_sections(self):
        self.assert_scaled_browser(
            "void draw_records_browser(", "void draw_browser(")
        body = function_body(
            self.records, "void draw_records_browser(", "void draw_browser(")
        for section in (
            "RecordsRootSection::Profiles",
            "RecordsRootSection::MultiplayerTournament",
            "CompletedRunRecordsView::Runs",
            "RECORDS / MULTIPLAYER",
            "SPLITS < %s >",
        ):
            self.assertIn(section, body)

    def test_local_runs_panel_scales_rows_and_splits(self):
        self.assert_scaled_browser(
            "void draw_browser(", "void draw_results_records_hint(")
        body = function_body(
            self.records, "void draw_browser(", "void draw_results_records_hint(")
        self.assertIn("row_count = 6", body)
        self.assertIn("split_row_y += 15", body)
        self.assertIn("ENTER / A  REPLAY", body)

    def test_records_shortcut_hints_share_density(self):
        hints = self.records.split("void draw_results_records_hint(", 1)[1]
        self.assertEqual(
            hints.count("resolve_modern_overlay_surface_scale("), 2)
        self.assertIn("8 * scale, height - 13 * scale", hints)
        self.assertIn("8 * scale, height - 28 * scale", hints)
        self.assertIn('"F8 / Y      RECORDS", 0xFFFFFFFFu, scale', hints)
        self.assertIn('"CTRL+B / X  LOCAL RUNS", 0xFFFFFFFFu, scale', hints)

    def test_results_panel_reserves_logical_hint_band(self):
        body = function_body(
            self.modern,
            "const int results_rows = results_menu_active",
            "const bool pause_subview_panel =")
        self.assertIn("constexpr int kResultsRecordsHintBand = 14;", body)
        self.assertIn("(8 + kResultsRecordsHintBand) * modal_scale", body)
        self.assertNotIn("8 * modal_scale - kResultsRecordsHintBand", body)


if __name__ == "__main__":
    unittest.main()
