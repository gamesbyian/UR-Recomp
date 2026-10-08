import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PATCH = ROOT / "tools" / "patches" / "snesrecomp-host-frame-hold.patch"
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


def _body(source, start, end):
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


class FrontendModalHoldContractTests(unittest.TestCase):
    def test_patch_holds_frames_without_becoming_a_pause(self):
        text = PATCH.read_text(encoding="utf-8")
        self.assertIn("+void snesrecomp_desktop_set_frame_hold(int held) {", text)
        self.assertIn("+int snesrecomp_desktop_frame_hold(void)", text)
        self.assertIn("+int snesrecomp_desktop_script_active(void) {", text)
        self.assertIn("+    const uint8 guest_frozen = g_paused || g_host_frame_hold;", text)
        self.assertIn("+    if (guest_frozen && !g_savestate_menu_hotkey", text)
        # snesrecomp_desktop_is_paused() keeps meaning "paused".
        self.assertNotIn("+int snesrecomp_desktop_is_paused", text)

    def test_patch_is_pinned(self):
        entry = json.loads(
            (ROOT / "tools" / "toolchain-entries" / "snesrecomp.json").read_text(
                encoding="utf-8"))
        paths = [patch["path"] for patch in entry["patches"]]
        self.assertIn("tools/patches/snesrecomp-host-frame-hold.patch", paths)
        self.assertLess(
            paths.index("tools/patches/snesrecomp-paused-overlay-present.patch"),
            paths.index("tools/patches/snesrecomp-host-frame-hold.patch"))

    def test_hold_policy_is_settled_main_menu_modals_only(self):
        source = HOST.read_text(encoding="utf-8")
        wanted = _body(source, "bool frontend_modal_hold_wanted() {",
                       "void update_frontend_modal_hold() {")
        for guard in ("!modern_mode()", "paused()", "g_ram[0x0313] == 0x01",
                      "g_ram[0x009F] != 0xD7", "practice_routing()",
                      "tour_continue_routing()", "g_practice_active"):
            self.assertIn(guard, wanted)
        for modal in ("g_practice_picker.visible", "g_progress_overview_visible",
                      "g_tour_action_visible", "g_frontend_options_active"):
            self.assertIn(modal, wanted)
        self.assertIn(
            "onboarding_surface_active() && !snesrecomp_desktop_script_active()",
            wanted)
        self.assertIn(
            "g_tour_action_visible && snesrecomp_desktop_script_active()",
            wanted)
        self.assertLess(
            wanted.index("g_tour_action_visible && snesrecomp_desktop_script_active()"),
            wanted.index("if (g_practice_picker.visible"),
            "Scripted tour must bypass hold before any modal is frozen")
        overlay = _body(source, 'extern "C" void ur_uniracers_modern_system_overlay(',
                        "if (onboarding_surface_active())")
        self.assertIn("update_frontend_modal_hold();", overlay)

    def test_diagnostics_end_with_real_newlines(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertNotIn('\\\\n"', source)


if __name__ == "__main__":
    unittest.main()
