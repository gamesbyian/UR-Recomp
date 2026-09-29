from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from rnc_method1 import BitReader, RNCError


class RNCBitReaderTests(unittest.TestCase):
    def test_declared_payload_boundary_is_hard(self):
        br = BitReader(b"\x01\x00TRAILING", 0, 2)
        self.assertEqual(br.read_bits(16), 1)
        with self.assertRaisesRegex(RNCError, "unexpected end"):
            br.read_bits(1)

    def test_invalid_bounds_rejected(self):
        with self.assertRaises(RNCError):
            BitReader(b"abc", 2, 1)


if __name__ == "__main__":
    unittest.main()
