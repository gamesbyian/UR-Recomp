"""Source-only adversarial tests; not evidence of an actual SDL capture."""
import unittest
from tools.check_modern_visual_capture_bundle import native_capture_matches


class NativeCaptureLogContractTest(unittest.TestCase):
    def test_real_shaped_source_line_accepted(self):
        self.assertTrue(native_capture_matches(
            "UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=1 guest_frame=1 "
            "output=1280x720 source=SDL_RenderReadPixels backend=sdl3", 1280, 720))

    def test_longer_source_and_output_values_are_rejected(self):
        for line in (
            "UR_MODERN_VISUAL_SDL_CAPTURE status=saved output=4x3 "
            "source=SDL_RenderReadPixelsFAKE",
            "UR_MODERN_VISUAL_SDL_CAPTURE status=saved output=4x30 "
            "source=SDL_RenderReadPixels",
        ):
            with self.subTest(line=line):
                self.assertFalse(native_capture_matches(line, 4, 3))

    def test_duplicate_or_malformed_fields_are_rejected(self):
        for suffix in (
            "status=saved status=failed output=4x3 source=SDL_RenderReadPixels",
            "status=failed status=saved output=4x3 source=SDL_RenderReadPixels",
            "status=saved output=4x3 output=4x3 source=SDL_RenderReadPixels",
            "status=saved output=4x3 source=SDL_RenderReadPixels source=other",
            "status=saved output=4x3 source=SDL_RenderReadPixels malformed",
        ):
            with self.subTest(suffix=suffix):
                self.assertFalse(native_capture_matches(
                    "UR_MODERN_VISUAL_SDL_CAPTURE " + suffix, 4, 3))

    def test_embedded_or_wrong_event_name_rejected(self):
        for prefix in ("prefixUR_MODERN_VISUAL_SDL_CAPTURE",
                       "LOG UR_MODERN_VISUAL_SDL_CAPTURE",
                       "UR_MODERN_VISUAL_SDL_CAPTURE_FAKE"):
            self.assertFalse(native_capture_matches(
                prefix + " status=saved output=4x3 source=SDL_RenderReadPixels", 4, 3))

    def test_wrong_capture_status_and_dimensions_rejected(self):
        for suffix in ("status=saved output=4x3 source=SDL_RenderCopy",
                       "status=failed output=4x3 source=SDL_RenderReadPixels",
                       "status=saved output=3x4 source=SDL_RenderReadPixels"):
            self.assertFalse(native_capture_matches(
                "UR_MODERN_VISUAL_SDL_CAPTURE " + suffix, 4, 3))

if __name__ == "__main__":
    unittest.main()
