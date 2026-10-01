#!/usr/bin/env python3
import unittest

from tools.classify_usa_beta_deltas import classify_pair, instruction_start
from snes2asm.disassembler import Disassembler


class UsaBetaDeltaClassifierTests(unittest.TestCase):
    def test_instruction_start_finds_opcode_for_operand(self):
        code_map = [
            Disassembler.NO_CODE,
            Disassembler.OP_CODE,
            Disassembler.OP_PARAM,
            Disassembler.OP_PARAM,
            Disassembler.NO_CODE,
        ]
        self.assertEqual(instruction_start(code_map, 1), 1)
        self.assertEqual(instruction_start(code_map, 2), 1)
        self.assertEqual(instruction_start(code_map, 3), 1)
        self.assertIsNone(instruction_start(code_map, 4))

    def test_classify_pair(self):
        self.assertEqual(classify_pair("opcode", "opcode", 10, 10), "opcode-byte-change")
        self.assertEqual(classify_pair("operand", "operand", 10, 10), "operand-byte-change")
        self.assertEqual(
            classify_pair("operand", "operand", 10, 11),
            "operand-boundary-disagreement",
        )
        self.assertEqual(
            classify_pair("unreached", "unreached", None, None),
            "unreached-by-snes2asm",
        )
        self.assertEqual(
            classify_pair("opcode", "unreached", 10, None),
            "reachability-disagreement",
        )
        self.assertEqual(
            classify_pair("opcode", "operand", 10, 9),
            "instruction-boundary-disagreement",
        )


if __name__ == "__main__":
    unittest.main()
