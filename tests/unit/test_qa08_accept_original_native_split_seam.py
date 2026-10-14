"""Adversarial 256x224 Snes9x RGB565/native RGB5 pixel seam evidence tests."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from tools import qa08_accept_original_native_split_seam as target


def source_frame():
    # Source RGB565 6-bit green 41 expands 166. Native 5-bit green20
    # expands 165; RGB5 source pixels are consequently the same.
    original=bytes((165,166,132,0))*(256*224)  # B,G,R,X
    native=bytes((132,165,165,0))*(256*224)    # R,G,B,A
    return original,native


class RealSourceSeamContractTests(unittest.TestCase):
    def test_original_6bit_green_to_native_5bit_witness(self):
        original,native=source_frame()
        report=target.rgb5_match(original,native,with_rows=True)
        self.assertEqual(report["identical_RGB5_expanded_pixels"],57344)
        self.assertEqual(report["different_pixels"],0)
        self.assertEqual(report["different_pixels_by_original_output_row"],[])
        self.assertIn(
            {"Snes9x_RGB8_green6":166,"native_RGB8_green5":165},
            report["Snes9x_green6_RGB8_to_native_green5_RGB8_unique_conversions"])

    def test_exact_full_256px_seam_rows_are_preserved_not_masked(self):
        original,native=map(bytearray,source_frame())
        for x in range(256):
            for y in (111,112):
                off=4*(y*256+x)
                original[off:off+3]=b"\x00\x00\x00"
            for y in (112,113):
                off=4*(y*256+x)
                native[off:off+3]=b"\x00\x00\x00"
        report=target.rgb5_match(original,native,with_rows=True)
        self.assertEqual(report["identical_RGB5_expanded_pixels"],56832)
        self.assertEqual(report["different_pixels"],512)
        self.assertEqual(report["different_pixels_by_original_output_row"],
                         [{"row":111,"different":256},{"row":113,"different":256}])

    def test_source_pixel_byte_or_format_forgery_fails(self):
        original,native=source_frame()
        bad=bytearray(original)
        bad[1]=167  # cannot be Snes9x six-bit green expanded byte
        with self.assertRaisesRegex(ValueError,"RGB565"):
            target.rgb5_match(bytes(bad),native)
        bad=bytearray(original)
        bad[3]=255
        with self.assertRaisesRegex(ValueError,"fourth component"):
            target.rgb5_match(bytes(bad),native)
        with self.assertRaisesRegex(ValueError,"byte count"):
            target.rgb5_match(original[:-4],native)

    def test_fake_accepted_archive_rejected_without_pixels(self):
        with tempfile.TemporaryDirectory() as tmp:
            one=Path(tmp)/"original.zip"
            two=Path(tmp)/"native.zip"
            one.write_bytes(b"not an original emulator run")
            two.write_bytes(b"not a native emulator run")
            with self.assertRaisesRegex(ValueError,"archive exact content SHA"):
                target.check(one,two)

if __name__=="__main__":
    unittest.main()
