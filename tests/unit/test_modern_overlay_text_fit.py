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
            ("R/PAD X  REPEAT PRACTICE", 24),
            ("R/PAD X  REMATCH", 24),
            ("CTRL+R   RETRY", 24),
            ("PRACTICE  ESC/B/START CANCEL", 28),
            ("CONTINUING  ESC/PAD B CANCEL", 28),
            ("PRACTICE START>EXIT FRONTEND", 28),
            ("MEDALS/RECORDS/TOUR STATE", 28),
            ("RETURN TO CLEAN STOCK DATA", 28),
            ("       PAD     KEY", 28),
            ("STUNTS END WHEEL-DOWN.", 28),
            ("F5/PAD X  QUICK PRACTICE", 28),
            ("F2/PAD X  RACERS (PICKER)", 28),
            ("ENTER/PAD A  OK   F1 HELP", 28),
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

    def test_onboarding_rows_are_fitted(self):
        source = HOST.read_text(encoding="utf-8")
        onboarding = _body(
            source, "if (onboarding_surface_active()) {\n        uint32_t*",
            "\n        return;\n    }\n",
        )
        self.assertIn("modern_overlay_text_cells(panel_w_logical)", onboarding)
        self.assertIn("fit_modern_overlay_text(row, text_cells)", onboarding)
        self.assertIn('"%-6s %-7s %s"', onboarding)


if __name__ == "__main__":
    unittest.main()
