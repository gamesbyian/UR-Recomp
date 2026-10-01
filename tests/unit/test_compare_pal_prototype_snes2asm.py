#!/usr/bin/env python3
import unittest

from tools.compare_pal_prototype_snes2asm import classify


class PalPrototypeAnalyzerTests(unittest.TestCase):
    def test_classification_order(self):
        self.assertEqual(classify("unreached","unreached",None,None,None,None),"unreached-both")
        self.assertEqual(classify("opcode","unreached",10,None,{},None),"reachability-disagreement")
        self.assertEqual(classify("operand","operand",10,11,{},{}),"instruction-boundary-disagreement")
        self.assertEqual(classify("opcode","opcode",10,10,{"opcode":"0xEA","m16":False,"x16":False},{"opcode":"0x60","m16":False,"x16":False}),"opcode-change")
        self.assertEqual(classify("opcode","opcode",10,10,{"opcode":"0xEA","m16":True,"x16":False},{"opcode":"0xEA","m16":False,"x16":False}),"mx-state-disagreement")
        self.assertEqual(classify("operand","operand",10,10,{"opcode":"0xA9","m16":False,"x16":False},{"opcode":"0xA9","m16":False,"x16":False}),"operand-or-literal-change")


if __name__ == "__main__":
    unittest.main()
