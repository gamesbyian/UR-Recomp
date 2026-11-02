"""WIDE-07 margin diagnostics must not masquerade as world-camera acceptance."""
import struct
import tempfile
import unittest
from pathlib import Path

from tools.check_widescreen_product_parity import check


def bmp(path, width, pixel):
    height = 224
    data = b''.join(b''.join(bytes((*pixel(x, y), 0)) for x in range(width))
                    for y in range(height))
    path.write_bytes(b'BM' + struct.pack('<IHHI', 54 + len(data), 0, 0, 54)
                     + struct.pack('<IiiHHIIiiII', 40, width, -height, 1, 32, 0,
                                   len(data), 0, 0, 0, 0) + data)


class MarginEvidenceTests(unittest.TestCase):
    def test_blank_and_coloured_margins_remain_diagnostic_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stock, wide = root / 'stock.bmp', root / 'wide.bmp'
            stock_wram, wide_wram = root / 'stock.bin', root / 'wide.bin'
            bmp(stock, 256, lambda x, y: (x % 251, y % 241, 71))
            stock_wram.write_bytes(bytes(0x20000))
            wide_wram.write_bytes(bytes(0x20000))
            pair = ('moving-race', stock, wide, stock_wram, wide_wram)
            for coloured in (False, True):
                with self.subTest(coloured=coloured):
                    bmp(wide, 342, lambda x, y: (x % 251, y % 241, 71)
                        if coloured and (x < 43 or x >= 299)
                        else ((x - 43) % 251, y % 241, 71)
                        if 43 <= x < 299 else (0, 0, 0))
                    result = check([pair])
                    self.assertEqual(result['outcome'], 'accepted')
                    center = result['metrics']['moving-race']['center']
                    margins = center['margin_activity']
                    for side in ('left', 'right'):
                        self.assertEqual(margins[side]['total_pixels'], 43 * 224)
                        self.assertEqual(margins[side]['nonblack_pixels'] > 0, coloured)
                        self.assertEqual(len(margins[side]['sha256']), 64)
                    self.assertEqual(margins['interpretation'],
                        'descriptive_only_not_source_world_or_camera_tile_proof')
                    self.assertEqual(result['metrics']['moving-race']['world_extension_verified'], False)


if __name__ == '__main__':
    unittest.main()
