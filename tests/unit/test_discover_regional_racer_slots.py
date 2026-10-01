#!/usr/bin/env python3
import unittest

from tools.discover_regional_racer_slots import (
    discover_abs_a_pairs,
    discover_abs_y_pairs,
    discover_dp_y_pairs,
)


class RegionalRacerSlotDiscoveryTests(unittest.TestCase):
    def test_abs_y_requires_both_directions(self):
        data = bytes.fromhex("AC B7 04 8C 9F 0F 00 AC 9F 0F 8C B7 04")
        pairs = discover_abs_y_pairs(data, 0x0F9F)
        self.assertEqual(list(pairs), [0x04B7])

    def test_abs_a_requires_both_directions(self):
        data = bytes.fromhex("AD CF 11 8D CD 11 00 AD CD 11 8D CF 11")
        pairs = discover_abs_a_pairs(data, 0x11CD)
        self.assertEqual(list(pairs), [0x11CF])

    def test_dp_y_requires_both_directions(self):
        data = bytes.fromhex("AC 11 04 84 A5 00 A4 A5 8C 11 04")
        pairs = discover_dp_y_pairs(data, 0xA5)
        self.assertEqual(list(pairs), [0x0411])


if __name__ == '__main__':
    unittest.main()
