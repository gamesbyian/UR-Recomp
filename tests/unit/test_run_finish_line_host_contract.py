import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


def _body(source, start, end):
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


class RunFinishLineHostContractTests(unittest.TestCase):
    def test_finish_is_the_line_crossing_snapshot_not_results_timer(self):
        source = HOST.read_text(encoding="utf-8")
        observe = _body(source, "void observe_run_finish_line() {",
                        "void observe_run_record_split() {")
        self.assertIn("ur_uniracers_read_line_snapshot(g_ram, 0x20000u, 0)", observe)
        self.assertIn("ur_uniracers_read_laps_remaining(g_ram, 0x20000u, 0) != 0", observe)
        self.assertIn("ur_uniracers_line_snapshot_ticks60(current_run_data(), snapshot)", observe)
        self.assertIn("if (!g_ram || g_run_finish_ticks60) return;", observe)

        completion = _body(source, "void complete_run_record_capture() {",
                           "const auto record =")
        self.assertIn("UR_RUN_RECORD FINISH_LINE_MISSING", completion)
        self.assertIn("*g_run_finish_ticks60", completion)
        # The shared timer keeps running after P1 finishes; RESULTS must not
        # be the source of the stored finish.
        self.assertNotIn("current_run_data()", completion)

        frame = _body(source, "if (run_active && g_run_capture.capturing()) {",
                      "if (g_surface == UR_UNIRACERS_RESTART_RESULTS &&")
        self.assertIn("observe_run_finish_line();", frame)

        begin = _body(source, "bool begin_run_record_capture(uint64_t host_frame) {",
                      "if (!run_record_capture_enabled()) return false;")
        self.assertIn("g_run_finish_ticks60.reset();", begin)

    def test_hud_presents_the_official_finish(self):
        source = HOST.read_text(encoding="utf-8")
        hud = _body(source, "void draw_run_timing_hud(", "if (!results && !finished && g_run_timing_last_split)")
        self.assertIn("const bool finished = g_run_finish_ticks60.has_value();", hud)
        self.assertIn("results || finished", hud)

    def test_results_default_is_first_row_until_player_moves(self):
        source = HOST.read_text(encoding="utf-8")
        refresh = _body(source, "void refresh_results_navigation_menu() {",
                        "bool results_navigation_active() {")
        self.assertIn("g_results_navigation_player_moved && i < next.row_count", refresh)
        nav = _body(source, "bool handle_results_navigation(",
                    "if (!ur_modern_host_navigation_is_confirm(action)) return false;")
        self.assertIn("g_results_navigation_player_moved = true;", nav)
        self.assertIn("g_results_navigation_player_moved = false;", source)


if __name__ == "__main__":
    unittest.main()
