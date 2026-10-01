#!/usr/bin/env python3
import unittest

from tools.verify_europe_semantic_edges import find_call_refs


class EuropeSemanticEdgeTests(unittest.TestCase):
    def test_find_call_refs_counts_same_bank_and_long_calls(self):
        blob = bytes.fromhex("00 20 B3 C5 00 22 B3 C5 81 00 20 B3 C5")
        refs = find_call_refs(blob, "81:C5B3")
        self.assertEqual([x["file_offset"] for x in refs["jsr"]], [1, 10])
        self.assertEqual([x["file_offset"] for x in refs["jsl"]], [5])


if __name__ == "__main__":
    unittest.main()
