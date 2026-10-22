"""A receipt-rehashed native log cannot substitute substring lookalikes for events."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from tests.unit.test_verify_modern_root_sdl_contrast import source_files
from tools import verify_modern_root_sdl_contrast as audit


class NativeEventFieldsTest(unittest.TestCase):
    def test_capture_event_fields_are_unique_and_exact(self):
        line = ("UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=40 "
                "output=1280x720 source=SDL_RenderReadPixels backend=sdl3")
        self.assertTrue(audit.native_capture_matches(line, 1280, 720))
        for spoiled in (
            line.replace("status=saved", "status=savedish"),
            line.replace("output=1280x720", "output=1280x720_spoof"),
            line.replace("source=SDL_RenderReadPixels",
                         "source=SDL_RenderReadPixelsFake"),
            line.replace("status=saved", "status=saved status=saved"),
            "prefix_" + line,
            line.replace("draw=40", "draw=40 unknown-field"),
        ):
            with self.subTest(spoiled=spoiled):
                self.assertFalse(audit.native_capture_matches(
                    spoiled, 1280, 720))

    def test_rehashed_capture_spoofs_do_not_validate_pixels(self):
        with tempfile.TemporaryDirectory() as temporary:
            receipt, png, p7, log = source_files(Path(temporary), wide=True)
            original = log.read_text(encoding="utf-8")
            self.assertTrue(audit.verify_capture(receipt, png, p7, log)[
                "source_root_contrast_verified"])
            for replaced in (
                original.replace("status=saved", "status=saved_but_forged"),
                original.replace("output=1280x720", "output=1280x720_EXTRA"),
                original.replace("source=SDL_RenderReadPixels",
                                 "source=SDL_RenderReadPixelsX"),
                original.replace("status=saved", "status=saved status=saved"),
                original.replace("painted=1 ", "painted=123 "),
            ):
                with self.subTest(replaced=replaced):
                    log.write_text(replaced, encoding="utf-8")
                    receipt["native_process_log_sha256"] = hashlib.sha256(
                        log.read_bytes()).hexdigest()
                    with self.assertRaisesRegex(ValueError, "missing actual"):
                        audit.verify_capture(receipt, png, p7, log)


if __name__ == "__main__":
    unittest.main()
