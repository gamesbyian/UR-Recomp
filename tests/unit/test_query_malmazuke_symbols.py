"""ROM-free regression tests for pinned malmazuke research address lookup."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from query_malmazuke_symbols import canonical_address, load_inputs, query, PIN


class MalmazukeLookupTests(unittest.TestCase):
    def test_address_canonicalization(self):
        self.assertEqual(canonical_address("$81:8050"), "81:8050")
        self.assertEqual(canonical_address("0x018050"), "81:8050")
        self.assertEqual(canonical_address("$7E:0126"), "$0126")
        self.assertEqual(canonical_address("$0126"), "$0126")
        with self.assertRaises(ValueError):
            canonical_address("81:80xx")

    def test_exact_source_candidate_and_no_promotion(self):
        symbols = {"schema_version": 1, "addresses": [
            {"address": "$81:8050", "region": "rom", "native": ["src/core/race_progress.cpp:update_checkpoints"]},
            {"address": "$0126", "region": "wram", "native": ["src/core/race.cpp:counter"]}]}
        links = {"schema_version": 1, "source": {"commit": PIN}, "entries": [
            {"pal": "81:8050", "domains": ["progress"], "pal_label": "sub_818050",
             "correspondence": {"status": "structural-interval-candidate",
                                "usa": "81:8050", "region": "checkpoint-finish/entry_time_prefix"}}]}
        match = query(symbols, links, address="81:8050")["matches"][0]
        self.assertEqual(match["usa_candidate"], "81:8050")
        self.assertFalse(match["verified_usa_semantics"])
        self.assertEqual(match["region_evidence"], "checkpoint-finish/entry_time_prefix")
        self.assertEqual(query(symbols, links, usa="81:8050")["total_matches"], 1)
        self.assertEqual(query(symbols, links, pattern="counter")["matches"][0]["pal"], "$0126")
        self.assertEqual(query(symbols, links, pattern="progress", limit=1)["total_matches"], 1)

    def test_fail_closed_and_no_ambiguous_promotion(self):
        symbols = {"addresses": [{"address": "$81:9999", "region": "rom", "native": []}]}
        links = {"entries": [{"pal": "81:9999", "correspondence": {"status": "not-covered"}}]}
        match = query(symbols, links, address="81:9999")["matches"][0]
        self.assertIsNone(match["usa_candidate"])
        self.assertFalse(match["verified_usa_semantics"])
        with self.assertRaises(ValueError):
            query(symbols, links, address="81:9999", usa="81:9999")
        with self.assertRaises(ValueError):
            query(symbols, links, pattern=".*", limit=0)

    def test_real_pinned_index_if_present(self):
        try:
            symbols, links = load_inputs()
        except FileNotFoundError:
            self.skipTest("pinned reference inputs absent from sparse checkout")
        result = query(symbols, links, address="81:8050")
        self.assertTrue(any("update_checkpoints" in p for row in result["matches"]
                            for p in row["native"]))
        self.assertTrue(all(not r["verified_usa_semantics"] for r in result["matches"]))
        self.assertEqual(result["source_commit"], PIN)


if __name__ == "__main__":
    unittest.main()
