#!/usr/bin/env python3
import unittest

from tools.verify_regional_racer_state_relations import inspect_build


class RegionalRacerStateRelationsTests(unittest.TestCase):
    def test_bidirectional_relation_requires_copy_in_and_copy_out(self):
        blob = bytearray(0x10000)
        # routine at file offset 0, synthetic LDY persistent/STY working then reverse
        blob[0:12] = bytes.fromhex('AC B7 04 8C 9F 0F AC 9F 0F 8C B7 04')
        spec = {
            "routine": "80:8000",
            "relations": {"X": ("04B7", "0F9F")},
        }
        result = inspect_build(bytes(blob), spec)
        rel = result["relations"]["X"]
        self.assertEqual(rel["copy_in_count"], 1)
        self.assertEqual(rel["copy_out_count"], 1)
        self.assertTrue(rel["bidirectional"])

    def test_one_way_relation_is_not_promoted(self):
        blob = bytearray(0x10000)
        blob[0:6] = bytes.fromhex('AC B7 04 8C 9F 0F')
        spec = {
            "routine": "80:8000",
            "relations": {"X": ("04B7", "0F9F")},
        }
        result = inspect_build(bytes(blob), spec)
        self.assertFalse(result["relations"]["X"]["bidirectional"])


if __name__ == "__main__":
    unittest.main()
