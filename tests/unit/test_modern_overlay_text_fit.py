import pathlib
import re
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


def _body(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


class ModernOverlayTextFitTests(unittest.TestCase):
    def test_fit_helper_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "modern-overlay-text-fit-test"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-I", str(ROOT / "native/product"),
                    str(ROOT / "tests/native/modern_overlay_text_fit_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)

    def test_controls_panel_lines_fit_the_panel(self):
        source = HOST.read_text(encoding="utf-8")
        controls = _body(
            source, "if (g_controls_visible) {\n            const int controls_h_logical",
            "if (g_quit_confirm_visible) {",
        )
        self.assertIn("modern_overlay_text_cells(panel_w_logical)", controls)
        # Dynamic lines (device, binding rows, both instruction lines) are
        # fitted; the only fixed literal is the 22-cell title.
        self.assertEqual(controls.count("fit_modern_overlay_text("), 4)
        literals = re.findall(r'"([A-Z][A-Z0-9 /=:+<>-]{3,})"', controls)
        self.assertIn("CONTROLS - KEYBOARD P1", literals)
        for text in literals:
            self.assertLessEqual(len(text), 24, text)
        self.assertNotIn("PAD: UP/DOWN A=REBIND", controls)

    def test_fixed_hints_fit_their_narrowest_panels(self):
        # (literal, cells): 24 for the shared 212-pixel pause-family panel and
        # results strip; 28 for 240-pixel panels and strips on a 256 frame.
        source = HOST.read_text(encoding="utf-8")
        expected = [
            ("REPEAT PRACTICE  R/X", 24),
            ("RETRY / REMATCH  R/X", 24),
            ("RECORDS  F8/Y", 24),
            ("UP/DN + CONFIRM", 24),
            ("PRACTICE  ESC/B/START CANCEL", 28),
            ("CONTINUING  ESC/PAD B CANCEL", 28),
            ("PRACTICE START>EXIT FRONTEND", 28),
            ("MEDALS/RECORDS/TOUR STATE", 28),
            ("RETURN TO CLEAN STOCK DATA", 28),
            ("ACTION PAD     KEY", 28),
            ("STUNTS END WHEEL-DOWN.", 28),
            ("F5/PAD X  QUICK PRACTICE", 28),
            ("F2/PAD X  RACERS (PICKER)", 28),
            ("F7/PAD L PROGRESS F1 HELP", 28),
            ("F9 CTRL F10/SELECT OPT", 28),
        ]
        for text, cells in expected:
            self.assertIn(f'"{text}"', source)
            self.assertLessEqual(len(text), cells, text)
        for retired in (
            "CTRL+R RETRY\"",
            "PRACTICE ROUTING...",
            "EXIT FRONTEND TO RETURN",
            "QUICK PRACTICE (MAIN MENU)",
            "WILL RETURN TO CLEAN STOCK DATA",
        ):
            self.assertNotIn(retired, source)

    def test_results_strip_clears_the_records_hint_band(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn(
            ": height - panel_h - 8 * modal_scale - kResultsRecordsHintBand;",
            source,
        )
        self.assertIn("constexpr int kResultsRecordsHintBand = 14;", source)
        browser = (ROOT / "native/product/completed_run_browser_host.cpp").read_text(
            encoding="utf-8"
        )
        hint = _body(browser, "void draw_results_records_hint(", "\n}\n")
        self.assertIn("8, height - 13,", hint)

    def test_onboarding_rows_are_fitted(self):
        source = HOST.read_text(encoding="utf-8")
        onboarding = _body(
            source, "if (onboarding_surface_active()) {\n        uint32_t*",
            "\n        return;\n    }\n",
        )
        self.assertIn("modern_overlay_text_cells(panel_w_logical)", onboarding)
        self.assertIn("fit_modern_overlay_text(row, text_cells)", onboarding)
        self.assertIn('"%-6s %-7s %s"', onboarding)


    def test_records_and_local_runs_lines_fit_their_panel(self):
        # Records and Local Runs share a 236-pixel panel: 27 Standard cells.
        cells = (236 - 2 * 8) // 8
        self.assertEqual(cells, 27)
        browser = (ROOT / "native/product/completed_run_browser_host.cpp").read_text(
            encoding="utf-8"
        )
        bodies = [
            _body(browser, "void draw_records_browser(", "\n}\n"),
            _body(browser, "void draw_browser(", "\n}\n"),
        ]
        for body in bodies:
            self.assertIn("width < 244 ? width - 12 : 236", body)
            self.assertIn("modern_overlay_text_cells(panel_w)", body)
            # Every line, fixed or composed, goes through the fitted drawer.
            self.assertEqual(body.count("snes_ovl_draw_text("), 1)
            self.assertIn("fit_modern_overlay_text(text, cells)", body)
            for text in re.findall(r'"((?:[^"\\]|\\.)*)"', body):
                if "%" not in text:
                    self.assertLessEqual(len(text), cells, text)

        # (format, representative long values): each composed row carries its
        # information inside the budget instead of relying on truncation.
        def expand(fmt, args):
            return re.sub(r"%(0?\d*)zu", r"%\1d", fmt) % args

        rows = [
            ("%c%c%-10.10s%3zu RUNS%3zu TRK", (">", "*", "MAXIMILIANRACERS", 99, 45)),
            ("%.16s%s", ("MAXIMILIANRACERS", "  * ACTIVE")),
            ("%zu RACERS %zu RUNS %zu UNAVAIL", (16, 99, 9)),
            ("%zu RACERS / %zu RUNS", (16, 999)),
            ("%zu TRACKS %zu RUNS %zu UNAVAIL", (45, 99, 9)),
            ("%zu TRACKS / %zu RUNS", (45, 999)),
            ("%zu MATCHES / %zu UNAVAILABLE", (99, 99)),
            ("%c %-12.12s %-12.12s", (">", "LITTLE DIPPER", "PLAYER 1 WIN")),
            ("COURSE %s", ("LITTLE DIPPER",)),
            ("RESULT %s", ("PLAYER 2 WIN",)),
            ("HEAD TO HEAD %zu MATCHES", (999,)),
            ("%c %-11.11s %2zu %s", (">", "LITTLE DIPPER", 99, "9:59.59/60")),
            ("PREV %s %s", ("9:59.59/60", "+9:59.59/60")),
            ("%zu RUNS  PB %s", (999, "9:59.59/60")),
            ("%c%3zu %s %s%s", (">", 999, "10-08", "9:59.59/60", " PB PV")),
            ("VS PB %s", ("+9:59.59/60",)),
            ("RUN #%03zu %s%s%s", (999, "2026-10-08", " PB", " PREV")),
            ("PB   %s %s", ("9:59.59/60", "+9:59.59/60")),
            ("SPLITS < %s > %zu-%zu/%zu", ("PREV", 10, 12, 12)),
            ("SPLITS < %s > CUR / DELTA", ("PREV",)),
            ("%-4s %s %s", ("CP12", "9:59.59/60", "+9:59.59/60")),
            ("%zu PLAYABLE / %zu STORED", (99, 99)),
            (" %3zu %s %s %s", (999, "10-08", "C45", "INCOMPATIBLE")),
            ("VS PB     %s", ("+9:59.59/60",)),
        ]
        for fmt, args in rows:
            self.assertIn(f'"{fmt}"', browser)
            self.assertLessEqual(len(expand(fmt, args)), cells, fmt)
        self.assertEqual(len("LOCAL RUNS / LITTLE DIPPER"), 26)
        # Titles keep the viewed track/racer whole: the RECORDS root goes
        # first, then the leading crumb is shortened.
        self.assertEqual(browser.count("records_title("), 4)
        self.assertIn('return number.size() < 2 ? "CP " + number : "CP" + number;', browser)
        for retired in (
            "LEFT / RIGHT  TRACKS / RACERS / MULTI",
            "RECORDS / MULTIPLAYER DETAIL",
            "%c %-12s %2zu RUNS %2zu TRACKS%s",
            "%c %-13s %2zu PB %s",
            "PREV %s  VS PB %s",
            "%c #%03zu %s %s %s%s",
            "CURRENT / TARGET / DELTA",
            "INVALID / UNBOUND PAIRS IGNORED",
        ):
            self.assertNotIn(retired, browser)


if __name__ == "__main__":
    unittest.main()
