import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PATCH = ROOT / "tools" / "patches" / "snesrecomp-paused-overlay-present.patch"
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
BROWSER_HOST = ROOT / "native" / "product" / "completed_run_browser_host.cpp"
UI_EVIDENCE = ROOT / ".github" / "workflows" / "native-ui-evidence.yml"


class PausedOverlayPresentContractTests(unittest.TestCase):
    def test_patch_presents_overlay_without_running_guest(self):
        text = PATCH.read_text(encoding="utf-8")
        added = "\n".join(
            line[1:] for line in text.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        )
        self.assertIn(
            "void snesrecomp_desktop_set_paused_overlay_presentation(int enabled)",
            added,
        )
        # The backdrop is captured before the title overlay so a paused
        # re-present never stacks overlays.
        backdrop = text.index("+        memcpy(g_paused_backdrop + (size_t)y")
        overlay = text.index(" if (g_game->system_overlay)\n     g_game->system_overlay(", backdrop)
        self.assertLess(backdrop, overlay)
        self.assertIn("static void PresentPausedSystemOverlay(void)", added)
        self.assertIn("+      PresentPausedSystemOverlay();\n       SDL_Delay(16);", text)
        self.assertIn('HostGetenv("PAUSED_OVERLAY_DUMP")', added)
        body = added[added.index("static void PresentPausedSystemOverlay(void)"):]
        body = body[:body.index("\n}\n")]
        for forbidden in ("RtlRunFrame", "RtlDrawPpuFrame", "draw_ppu_frame", "g_ram"):
            self.assertNotIn(forbidden, body)

    def test_patch_is_pinned_in_both_manifests(self):
        entry = json.loads(
            (ROOT / "tools" / "toolchain-entries" / "snesrecomp.json").read_text(
                encoding="utf-8"))
        paths = [patch["path"] for patch in entry["patches"]]
        self.assertIn("tools/patches/snesrecomp-paused-overlay-present.patch", paths)
        self.assertIn(
            "tools/patches/snesrecomp-paused-overlay-present.patch",
            (ROOT / "tools" / "toolchain.json").read_text(encoding="utf-8"),
        )

    def test_modern_host_opts_in_and_authentic_does_not(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn(
            "snesrecomp_desktop_set_paused_overlay_presentation(modern_mode() ? 1 : 0);",
            source,
        )

    def test_records_hint_yields_to_pause_subviews(self):
        source = BROWSER_HOST.read_text(encoding="utf-8")
        start = source.index("void draw_browser_hint(")
        body = source[start:source.index("\n}\n", start)]
        self.assertIn("ur_uniracers_modern_subview_active()", body)

    def test_native_ui_evidence_asserts_the_paused_present(self):
        workflow = UI_EVIDENCE.read_text(encoding="utf-8")
        self.assertIn('export SNESRECOMP_PAUSED_OVERLAY_DUMP="', workflow)
        self.assertIn(
            'python3 tools/check_paused_overlay_dump.py "$PAUSED_OVERLAY"', workflow)
        self.assertIn('- "tools/patches/snesrecomp-paused-overlay-present.patch"', workflow)


if __name__ == "__main__":
    unittest.main()
