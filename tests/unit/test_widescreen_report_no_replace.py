"""WIDE-07 CLI reports must not replace retained capture or evidence files."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import check_widescreen_product_parity as parity


def bmp(path: Path, width: int, height: int) -> None:
    stride = width * 4
    header = b'BM' + struct.pack('<IHHI', 54 + stride * height, 0, 0, 54)
    dib = struct.pack('<IiiHHIIiiII', 40, width, -height, 1, 32, 0,
                      stride * height, 0, 0, 0, 0)
    path.write_bytes(header + dib + bytes(stride * height))


class WidescreenReportNoReplaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.stock = self.root / 'stock'
        self.wide = self.root / 'wide'
        self.stock.mkdir()
        self.wide.mkdir()
        bmp(self.stock / 'frame.fb.bmp', 256, 224)
        bmp(self.wide / 'frame.fb.bmp', 342, 224)
        for folder in (self.stock, self.wide):
            (folder / 'frame.wram.bin').write_bytes(bytes(0x20000))
        self.out = self.root / 'parity.json'

    def run_cli(self):
        argv = ['check_widescreen_product_parity.py', '--stock-dumps', str(self.stock),
                '--wide-dumps', str(self.wide), '--checkpoint', 'frame',
                '--out', str(self.out)]
        with patch.object(sys, 'argv', argv), redirect_stdout(io.StringIO()):
            return parity.main()

    def test_new_report_complete_then_refuses_replacement(self):
        self.assertEqual(self.run_cli(), 0)
        before = self.out.read_bytes()
        self.assertIn(b'"outcome": "accepted"', before)
        with self.assertRaises(FileExistsError):
            self.run_cli()
        self.assertEqual(self.out.read_bytes(), before)
        self.assertFalse(list(self.root.glob('.ur-report-stage-*')))

    def test_existing_foreign_file_is_preserved(self):
        self.out.write_bytes(b'FOREIGN ORIGINAL EVIDENCE')
        with self.assertRaises(FileExistsError):
            self.run_cli()
        self.assertEqual(self.out.read_bytes(), b'FOREIGN ORIGINAL EVIDENCE')

    def test_symlink_target_is_preserved(self):
        target = self.root / 'source-image.png'
        target.write_bytes(b'RETAIN SOURCE')
        try:
            self.out.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        with self.assertRaises(FileExistsError):
            self.run_cli()
        self.assertTrue(self.out.is_symlink())
        self.assertEqual(target.read_bytes(), b'RETAIN SOURCE')

    def test_existing_empty_directory_is_preserved(self):
        self.out.mkdir()
        with self.assertRaises(FileExistsError):
            self.run_cli()
        self.assertTrue(self.out.is_dir())
        self.assertEqual(list(self.out.iterdir()), [])

    def test_output_aliasing_a_consumed_capture_does_not_destroy_it(self):
        self.out = self.stock / 'frame.fb.bmp'
        original = self.out.read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_cli()
        self.assertEqual(self.out.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
