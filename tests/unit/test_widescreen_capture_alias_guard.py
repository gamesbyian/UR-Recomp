"""Source-file independence for stock/wide parity evidence."""
import os
import struct
import tempfile
import unittest
from pathlib import Path

from tools.check_widescreen_product_parity import check


def write_bmp(path: Path, width: int) -> None:
    height = 224
    data = bytes(width * 4 * height)
    path.write_bytes(
        b"BM" + struct.pack("<IHHI", 54 + len(data), 0, 0, 54)
        + struct.pack("<IiiHHIIiiII", 40, width, -height, 1, 32, 0,
                      len(data), 0, 0, 0, 0) + data
    )


class WidescreenCaptureAliasGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.stock_fb = self.root / "stock.bmp"
        self.wide_fb = self.root / "wide.bmp"
        self.stock_wram = self.root / "stock.bin"
        self.wide_wram = self.root / "wide.bin"
        write_bmp(self.stock_fb, 256)
        write_bmp(self.wide_fb, 342)
        self.stock_wram.write_bytes(bytes(0x20000))
        self.wide_wram.write_bytes(bytes(0x20000))

    def pair(self, tag="cp", *, stock_fb=None, wide_fb=None,
             stock_wram=None, wide_wram=None):
        return (tag, stock_fb or self.stock_fb, wide_fb or self.wide_fb,
                stock_wram or self.stock_wram, wide_wram or self.wide_wram)

    def test_distinct_equal_wram_bytes_are_valid(self):
        self.assertEqual(check([self.pair()])["outcome"], "accepted")

    def test_same_wram_path_cannot_serve_both_runs(self):
        with self.assertRaisesRegex(ValueError, "capture source reused.*aliases"):
            check([self.pair(wide_wram=self.stock_wram)])

    def test_hardlinked_wram_alias_cannot_serve_both_runs(self):
        alias = self.root / "hardlink.bin"
        try:
            os.link(self.stock_wram, alias)
        except OSError as exc:
            self.skipTest(f"filesystem cannot create hardlinks: {exc}")
        with self.assertRaisesRegex(ValueError, "capture source reused.*aliases"):
            check([self.pair(wide_wram=alias)])

    def test_symlinked_wram_alias_cannot_serve_both_runs(self):
        alias = self.root / "symlink.bin"
        try:
            alias.symlink_to(self.stock_wram)
        except OSError as exc:
            self.skipTest(f"filesystem cannot create symlinks: {exc}")
        with self.assertRaisesRegex(ValueError, "capture source reused.*aliases"):
            check([self.pair(wide_wram=alias)])

    def test_reused_frame_between_tags_rejected_even_when_wram_changes(self):
        second_stock_wram = self.root / "second-stock.bin"
        second_wide_wram = self.root / "second-wide.bin"
        second_stock_wram.write_bytes(bytes(0x20000))
        second_wide_wram.write_bytes(bytes(0x20000))
        # The old four-hash fingerprint differed if one capture changed, even
        # though the same BMP files were relabelled as a second checkpoint.
        with self.assertRaisesRegex(ValueError, "capture source reused.*aliases"):
            check([self.pair("frame-1"), self.pair("frame-2",
                stock_wram=second_stock_wram, wide_wram=second_wide_wram)])


if __name__ == "__main__":
    unittest.main()
