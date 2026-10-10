"""Fail-closed contracts for REAL SDL physical 3840x2160 output capture."""
import tempfile
from pathlib import Path
import unittest

from tools.baldosa_sdl_physical_4k_capture_spike import (
    MARK, ANCHOR, IMPLEMENTATION, OSD_ANCHOR,
    OSD_REPLACEMENT, patch_host, stage
)


class RealSdlPhysicalCapturePatchTests(unittest.TestCase):
    def base(self):
        return ("#include <stdint.h>\n"
                + OSD_ANCHOR + "\n}\n"
                "static void SdlRenderer_EndDraw(void) {\n"
                + ANCHOR
                + "}\n\nstatic void SdlRenderer_Reconfigure(void) {}\n")

    def test_stages_once_at_real_native_present_boundary(self):
        candidate = patch_host(self.base())
        self.assertEqual(candidate.count(MARK), 1)
        self.assertEqual(patch_host(candidate), candidate)
        self.assertLess(candidate.index("UrBaldosaReadActual4kDrawable();"),
                        candidate.index("SDL_RenderPresent(g_renderer);"))
        self.assertIn("SDL_RenderReadPixels(g_renderer, NULL,", candidate)
        self.assertIn("w != 3840 || h != 2160", candidate)
        self.assertIn("target != g_present_frame", candidate)
        self.assertIn("TUPLTYPE RGB_ALPHA", candidate)
        self.assertIn("ur4k_target == g_present_frame", candidate)
        self.assertIn("snes_osd_present_done();", candidate)
        self.assertNotIn(OSD_ANCHOR, candidate)
        self.assertIn("const char *ur4k_file", OSD_REPLACEMENT)

    def test_dual_real_output_capture_uses_independent_one_shot_frames(self):
        candidate = patch_host(self.base())
        self.assertIn('UR_BALDOSA_PHYSICAL_4K_CAPTURE_EXTRA_FRAME', candidate)
        self.assertIn('UR_BALDOSA_PHYSICAL_4K_CAPTURE_EXTRA_FILE', candidate)
        self.assertIn("static int done[2] = {0, 0};", candidate)
        self.assertIn("for (int capture = 0; capture < 2; ++capture)", candidate)
        self.assertIn("if (done[capture]) continue;", candidate)
        self.assertIn("done[capture] = 1;", candidate)
        self.assertIn("for (int ur4k_i = 0; ur4k_i < 2; ++ur4k_i)", candidate)
        self.assertEqual(candidate.count("UrBaldosaReadActual4kDrawable();"), 1)
        self.assertEqual(candidate.count(MARK), 1)
        self.assertIn("ur4k_target >= 2000 && ur4k_target <= 2450", candidate)
        self.assertIn("target < 2000 || target > 2450", candidate)
        self.assertIn("strcmp(path, getenv(path_keys[0])", candidate)
        self.assertIn("target != g_present_frame", candidate)
        self.assertIn("ur4k_target == g_present_frame", candidate)
        self.assertLess(candidate.index("UrBaldosaReadActual4kDrawable();"),
                        candidate.index("SDL_RenderPresent(g_renderer);"))

    def test_no_source_renderer_or_texture_dump_substitution(self):
        c = patch_host(self.base())
        self.assertIn("snesrecomp_sdl_get_render_output_size(g_renderer", c)
        self.assertIn("SDL_PIXELFORMAT_ARGB8888", c)
        self.assertIn("source=SDL_RenderReadPixels", c)
        self.assertNotIn("SDL_RenderReadPixels(g_texture", c)
        self.assertIn("#if !SNESRECOMP_SDL3", c)
        self.assertNotIn("UR_RACER_HD_UNSAFE", IMPLEMENTATION)

    def test_unknown_abi_fails_closed(self):
        with self.assertRaises(ValueError):
            patch_host("static void SdlRenderer_EndDraw(void) {}\n")
        with self.assertRaises(ValueError):
            patch_host(self.base().replace(ANCHOR, "SDL_RenderPresent(g_renderer);"))
        with self.assertRaises(ValueError):
            patch_host(self.base() + ANCHOR)
        with self.assertRaises(ValueError):
            patch_host(self.base().replace(
                "static void SdlRenderer_EndDraw(void)",
                "static void Foo(void)"))

    def test_rejects_ambiguous_preexisting_marker(self):
        with self.assertRaises(ValueError):
            patch_host(self.base() + MARK + MARK)

    def test_stages_disposable_tree_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            host = root / "runner/src/desktop/host_main.c"
            host.parent.mkdir(parents=True)
            host.write_text(self.base(), encoding="utf-8")
            self.assertTrue(stage(root))
            self.assertFalse(stage(root))
            self.assertIn(MARK, host.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
