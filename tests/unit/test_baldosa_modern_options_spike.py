#!/usr/bin/env python3
"""The native Options host seam is narrow, guarded, atomic and idempotent."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import baldosa_modern_options_spike as seam

ROOT = Path(__file__).resolve().parents[2]

HOST_STUB = (
    "static bool g_volume_changed;\n"
    "static bool g_fullscreen_changed;\n"
    "static const char *g_active_config_file;\n"
    "static int VSyncInterval(void) { return 1; }\n"
    "static void ApplyLiveSettings(const Config *before) {\n}\n\n"
    + seam.ANCHOR + "static void Next(void) {}\n"
)


class BaldosaModernOptionsSpikeTests(unittest.TestCase):
    def test_seam_is_idempotent_and_exports_only_four_bounded_functions(self):
        staged = seam.patch_host_main(HOST_STUB)
        self.assertEqual(seam.patch_host_main(staged), staged)
        self.assertEqual(staged.count(seam.MARK), 1)
        for name in ("snesrecomp_desktop_product_get_display",
                     "snesrecomp_desktop_product_apply_display",
                     "snesrecomp_desktop_product_get_volume",
                     "snesrecomp_desktop_product_set_volume"):
            self.assertEqual(staged.count("int " + name + "("), 1, name)
        # Out-of-range requests are refused, never clamped silently.
        self.assertIn("fullscreen < 0 || fullscreen > 2", staged)
        self.assertIn("vsync < 0 || vsync > 2", staged)
        self.assertIn("percent < 0 || percent > 100", staged)
        # The seam sits AFTER the statics it uses and before the next code.
        self.assertLess(staged.index("static void ApplyLiveSettings"),
                        staged.index("snesrecomp_desktop_product_apply_display"))
        # Volume is made durable at once, so a hard kill keeps what was heard.
        self.assertIn("WriteConfigFile(g_active_config_file)", staged)
        # No guest, simulation, input or save code is reachable from here.
        for forbidden in ("RtlRunFrame", "g_ram", "g_sram", "SetPadButton",
                          "RtlWriteSram", "keybinds_init"):
            self.assertNotIn(forbidden, staged.split(seam.MARK, 1)[1]
                             .split(seam.ANCHOR)[0], forbidden)

    def test_a_moved_pinned_host_is_rejected_without_partial_change(self):
        for needed in ("static bool g_volume_changed;\n",
                       "static int VSyncInterval(void) { return 1; }\n",
                       seam.ANCHOR):
            with self.assertRaisesRegex(ValueError, "diverged"):
                seam.patch_host_main(HOST_STUB.replace(needed, ""))
        with self.assertRaisesRegex(ValueError, "diverged"):
            seam.patch_host_main(HOST_STUB + seam.ANCHOR)  # ambiguous anchor
        header = "int snesrecomp_desktop_frame_width(void);\n"
        staged = seam.patch_host_header(header)
        self.assertEqual(seam.patch_host_header(staged), staged)
        self.assertIn("snesrecomp_desktop_product_set_volume", staged)
        with self.assertRaisesRegex(ValueError, "diverged"):
            seam.patch_host_header("")

    def test_plan_changes_nothing_when_any_file_is_missing(self):
        with tempfile.TemporaryDirectory() as d:
            game = Path(d)
            host = game / "snesrecomp/runner/src/desktop/host_main.c"
            host.parent.mkdir(parents=True)
            host.write_text(HOST_STUB, encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                seam.plan(game)
            self.assertEqual(host.read_text(encoding="utf-8"), HOST_STUB)

    def test_native_root_binds_the_seam_and_hides_nothing_it_cannot_do(self):
        root = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text()
        for name in ("snesrecomp_desktop_product_get_display",
                     "snesrecomp_desktop_product_apply_display",
                     "snesrecomp_desktop_product_get_volume",
                     "snesrecomp_desktop_product_set_volume"):
            self.assertIn(name, root)
        self.assertIn("ModernRootDestination::Options", root.split(
            "kNativeRootAvailable", 1)[1].split(";", 1)[0])
        model = (ROOT / "native/product/baldosa_native_options.hpp").read_text()
        # Truthfulness: controls the pinned host does not honour are absent.
        for absent in ("vibration", "pause_on_focus", "widescreen",
                       "render_scale", "output_resolution", "presentation_fps",
                       "ghost"):
            self.assertNotIn("BaldosaOptionsRow::" + absent.title(), model)
        self.assertIn("options-v1.txt", model)
        # The active-racer selector file is never touched by a settings write.
        self.assertNotIn("host-state-v1.txt",
                         model.split("namespace ur::product {", 1)[1])


if __name__ == "__main__":
    unittest.main()
