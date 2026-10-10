"""WRAM address labels are tentative and may not launder guest parity."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import annotate_bowl_guest_memory_offsets as a


class BowlSymbolMappingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.symbols = a.parse_ram_symbols(a.RAM_SYMBOLS.read_text())

    def frame(self, addrs=("0x0009F", "0x10020"), total=None, truncated=False):
        if total is None:
            total = len(addrs)
        return {
            "offset_from_actual_tally_host_frame": 54,
            "absolute_host_frame": 4333,
            "different_guest_bytes": {"wram": total, "vram": 0, "cgram": 0},
            "differing_byte_offsets_by_memory_class": {
                "wram": {"addresses": list(addrs),
                         "total": total, "truncated": truncated}},
        }

    def report(self, frame):
        return {
            "schema": "UR-QA01-BOWL-TALLY-ANCHORED-PHASE/1",
            "release_complete_event_credit": 0,
            "retains_raw_guest_memory": False,
            "offset_profile_cap_per_memory_class": 128,
            "same_host_frame_samples": [dict(frame) for _ in range(8)],
        }

    def test_pinned_catalog_parses_original_wram_symbols(self):
        self.assertGreater(len(self.symbols), 400)
        menu = a.lookup(0x009F, self.symbols)
        self.assertEqual(menu["snes_wram"], "7E:009F")
        self.assertTrue(menu["most_specific_containing_symbols"])
        high = a.lookup(0x10020, self.symbols)
        self.assertEqual(high["snes_wram"], "7F:0020")
        self.assertIn("source labels", menu["interpretation"])

    def test_synthetic_full_report_stays_read_only_and_zero_credit(self):
        doc = a.annotate(self.report(self.frame()), self.symbols)
        self.assertEqual(doc["schema"], "UR-QA01-BOWL-WRAM-OFFSET-SOURCE-LABELS/1")
        self.assertEqual(doc["release_complete_event_credit"], 0)
        self.assertTrue(doc["read_only"])
        self.assertFalse(doc["raw_guest_memory_included"])
        self.assertFalse(doc["any_incomplete_address_profile"])
        self.assertEqual(len(doc["frames"]), 8)
        self.assertEqual([x["snes_wram"] for x in doc["frames"][0]["mapped_addresses"]],
                         ["7E:009F", "7F:0020"])
        self.assertNotIn("original_byte", json.dumps(doc))
        self.assertNotIn("native_byte", json.dumps(doc))

    def test_missing_or_forged_offsets_and_acceptance_rejected(self):
        cases = [
            ({"release_complete_event_credit": 1}, "zero acceptance"),
            ({"retains_raw_guest_memory": True}, "raw guest"),
            ({"offset_profile_cap_per_memory_class": 0}, "bounded offset"),
            ({"same_host_frame_samples": []}, "eight"),
        ]
        for overrides, message in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaisesRegex(ValueError, message):
                    a.annotate(dict(self.report(self.frame()), **overrides),
                               self.symbols)
        for addresses, count, truncated in [
            (["0x0009F", "0x0009F"], 2, False),
            (["0x20000"], 1, False),
            (["0x9F"], 1, False),
            (["0x10020", "0x0009F"], 2, False),
            (["0x0009F"], 2, False),
            (["0x0009F"], 1, True),
        ]:
            with self.subTest(addresses=addresses):
                with self.assertRaises(ValueError):
                    a.annotate(self.report(self.frame(addresses, count, truncated)),
                               self.symbols)
        overflow = [f"0x{i:05X}" for i in range(128)]
        r = a.annotate(self.report(self.frame(overflow, 129, True)), self.symbols)
        self.assertTrue(r["any_incomplete_address_profile"])
        self.assertEqual(len(r["frames"][0]["mapped_addresses"]), 128)
        self.assertEqual(r["release_complete_event_credit"], 0)

    def test_invalid_source_symbols_are_not_silent(self):
        with self.assertRaisesRegex(ValueError, "invalid pinned"):
            a.parse_ram_symbols("this is not a RAM symbol")
        with self.assertRaisesRegex(ValueError, "invalid pinned WRAM"):
            a.parse_ram_symbols("7FFFFF wBeyond 2 ; crosses WRAM end")
        self.assertEqual(a.parse_ram_symbols("770000 sSramVar 2"), [])


if __name__ == "__main__":
    unittest.main()
