import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
HARNESS = ROOT / "tests" / "native" / "run_modern_pad_glyph_acceptance.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "modern-onboarding-practice-acceptance.yml"
ONBOARDING_PATHS = ROOT / ".github" / "ci" / "modern-native-onboarding-paths.txt"


def _body(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


class ModernPadGlyphContractTests(unittest.TestCase):
    def test_glyphs_come_from_the_live_gamepad_map(self):
        source = HOST.read_text(encoding="utf-8")
        label = _body(
            source, "std::string live_gamepad_binding_label(int control_offset) {", "\n}\n"
        )
        self.assertIn("modern_pad_glyph_for_control(", label)
        self.assertIn("FindCmdForGamepadButton(button, 0)", label)
        self.assertIn("kKeys_Controls", label)
        # No hard-coded SNES-letter table, no brand guessing.
        self.assertNotIn('case 7: return "B";', label)
        self.assertNotIn("SDL_GetGamepadType", label)
        # config.h is a C header; its lookup needs C linkage.
        self.assertIn('extern "C" {\n#include "desktop/config.h"\n}', source)

    def test_controls_hints_use_live_glyphs(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn("const ur::product::ModernControlsPadGlyphs pad_glyphs{", source)
        self.assertIn("g_controls_rebind, key_labels, pad_glyphs);", source)

    def test_tour_confirm_hints_use_live_glyphs(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn(
            '"ENTER / PAD " + live_gamepad_binding_label(6) + " CONFIRM"', source
        )
        self.assertIn(
            '"ESC / PAD " + live_gamepad_binding_label(7) + " CANCEL"', source
        )
        self.assertNotIn('"ENTER / PAD A CONFIRM"', source)

    def test_native_acceptance_is_wired(self):
        subprocess.run(["bash", "-n", str(HARNESS)], cwd=ROOT, check=True)
        harness = HARNESS.read_text(encoding="utf-8")
        for marker in (
            "pad_jump=A pad_brake=X pad_a=B pad_x=Y pad_l=LB pad_r=RB",
            "Start, B, R2, Y, X, Lb, Rb$",
            'grep -q " pad_jump=RT\\( \\|$\\)"',
        ):
            self.assertIn(marker, harness)
        workflow = WORKFLOW.read_text(encoding="utf-8")
        paths = ONBOARDING_PATHS.read_text(encoding="utf-8")
        self.assertIn("run_modern_pad_glyph_acceptance.sh", workflow)
        self.assertIn("native/product/modern_pad_glyphs.hpp", paths)


if __name__ == "__main__":
    unittest.main()
