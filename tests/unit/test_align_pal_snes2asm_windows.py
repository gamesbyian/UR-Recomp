#!/usr/bin/env python3
import unittest

from tools.align_pal_snes2asm_windows import best_shift


class PalSnes2asmHomologAlignmentTests(unittest.TestCase):
    def test_best_shift_finds_relocated_copy(self):
        src=bytes(range(64))
        dst=bytes([0xFF])*5 + src + bytes([0xEE])*7
        shift,score=best_shift(src,dst,0,31,radius=8)
        self.assertEqual(shift,5)
        self.assertEqual(score,1.0)


if __name__=="__main__": unittest.main()
