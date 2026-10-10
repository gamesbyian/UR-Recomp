"""Fixed-Original native 1x source capture must be an isolated observer."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class FixedOriginalNativeSourceTests(unittest.TestCase):
    def test_source_capture_uses_original_field_before_compositor(self):
        source = (ROOT / "tools" / "baldosa_native_racer_presentation.cpp").read_text()
        self.assertIn('std::getenv("UR_BALDOSA_FIXED_ORIGINAL_SOURCE_FRAME")', source)
        self.assertIn("width != 256 || height != 224", source)
        self.assertIn("frame != g_frame", source)
        self.assertIn("g_original_source_saved_frame == g_frame", source)
        self.assertIn('width, height, g_frame, "ur-baldosa-original-source"', source)
        self.assertIn("source=native-original-ppu", source)
        entry = source.index("extern \"C\" int ur_baldosa_hd_draw_frame(")
        call = source.index("capture_fixed_original_source(field, frame_w, frame_h);", entry)
        compositor = source.index("racer_hd_draw_frame(", entry)
        self.assertLess(call, compositor)
        self.assertIn("if (!enabled()) return 0;", source[entry:call])
        body = source[source.index("void capture_fixed_original_source("):
                      source.index("// Compare the actual composited raster")]
        for forbidden in ("RemoveFromGame", "g_ram[", "g_cpu.", "PpuSetOverlay",
                          "UR_RACER_HD_UNSAFE"):
            self.assertNotIn(forbidden, body)

    def test_capture_is_not_mistaken_for_rendering_admission(self):
        source = (ROOT / "tools" / "baldosa_native_racer_presentation.cpp").read_text()
        self.assertIn("const bool saved = save_presented_pam(", source)
        self.assertIn("g_original_source_saved_frame = g_frame", source)
        self.assertIn("if (scale == 1) return 0;", source)
        self.assertIn("compose_nearest_density_frame(", source)


if __name__ == "__main__":
    unittest.main()
