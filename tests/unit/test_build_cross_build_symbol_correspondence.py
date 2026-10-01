#!/usr/bin/env python3
import unittest

from tools.build_cross_build_symbol_correspondence import (
    build_ram_correspondences,
    parse_usa_ram_address,
)


class CrossBuildSymbolCorrespondenceTests(unittest.TestCase):
    def test_parse_usa_ram_address(self):
        self.assertEqual(parse_usa_ram_address("7E:0411"), "0411")
        self.assertEqual(parse_usa_ram_address("`7E:0F9F`"), "0F9F")
        self.assertIsNone(parse_usa_ram_address("7F:0000"))

    def test_ram_tiers_require_repeated_anchor_support(self):
        symbols = {"entries": [
            {"kind": "ram", "address": "7E:0411", "name": "Player1_XPosition", "confidence": 5},
            {"kind": "ram", "address": "7E:0F9F", "name": "CurrentPlayer_XVelocityWorking", "confidence": 4},
        ]}
        atlas = {"field_consistency": [
            {
                "consistent": True, "usa_word": "0411", "candidate_words": ["0415"],
                "deltas": [4], "build": "europe-retail", "anchors": ["A", "B"],
            },
            {
                "consistent": True, "usa_word": "0F9F", "candidate_words": ["0FA3"],
                "deltas": [4], "build": "pal-prototype-1994-11-29", "anchors": ["C"],
            },
        ]}
        rows = build_ram_correspondences(symbols, atlas)
        by_name = {r["name"]: r for r in rows}
        self.assertEqual(by_name["Player1_XPosition"]["evidence_tier"], "strong")
        self.assertEqual(by_name["CurrentPlayer_XVelocityWorking"]["evidence_tier"], "candidate")


if __name__ == "__main__":
    unittest.main()
