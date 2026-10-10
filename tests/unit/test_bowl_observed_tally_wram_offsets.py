"""Executed QA-01 Bowl original/native offsets, not synthetic memory parity."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import annotate_bowl_guest_memory_offsets as annotator

OBSERVED = ROOT / "analysis/data/bowl-original-native-observed-tally-wram-offsets-20261010.json"
PREVIOUS = ROOT / "analysis/data/bowl-tally-full-guest-same-host-eight-frame-20261009.json"


class ExecutedBowlAddressWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.witness = json.loads(OBSERVED.read_text(encoding="utf-8"))
        cls.phase = cls.witness["tally_anchored_guest_phase"]
        cls.previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
        cls.rows = cls.phase["same_host_frame_samples"]

    def test_exact_pinned_original_and_native_provenance(self):
        self.assertEqual(self.witness["schema"], "UR-QA01-BOWL-SOURCED-OFFSET-CAPTURE/1")
        self.assertEqual(self.witness["provenance"]["workflow_run_id"], 38025090532)
        self.assertEqual(self.witness["provenance"]["artifact_id"], 11659973901)
        self.assertEqual(self.witness["provenance"]["artifact_zip_sha256"],
                         "5fc790a32137576f6b2d796f9fbfb68d417c910a11b0e51a83c1950f0d53d62b")
        self.assertEqual(self.witness["release_complete_event_credit"], 0)
        self.assertEqual(self.phase["release_complete_event_credit"], 0)
        self.assertFalse(self.phase["retains_raw_guest_memory"])
        self.assertEqual(self.phase["reference_and_native_tally_host_frame"], 4279)
        self.assertEqual(self.phase["reference_and_native_result_host_frame"], 4349)
        self.assertEqual(self.phase["whole_guest_memory_bytes_per_capture"], 197120)

    def test_each_real_host_sample_matches_previously_independent_count_witness(self):
        self.assertEqual(len(self.rows), len(self.previous["phase_samples"]))
        for row, old in zip(self.rows, self.previous["phase_samples"]):
            offset = row["offset_from_actual_tally_host_frame"]
            self.assertEqual(offset, old["tally_offset"])
            self.assertEqual(row["absolute_host_frame"], old["host_frame"])
            self.assertEqual(row["absolute_host_frame"], 4279 + offset)
            for old_class, new_class in (("wram", "wram"), ("vram", "vram"),
                                         ("cgram", "cgram")):
                profile = row["differing_byte_offsets_by_memory_class"][new_class]
                count = row["different_guest_bytes"][new_class]
                self.assertEqual(count, old["guest_different_bytes"][old_class])
                self.assertEqual(len(profile["addresses"]), count)
                self.assertEqual(profile["total"], count)
                self.assertFalse(profile["truncated"])
                self.assertEqual(profile["addresses"], sorted(set(profile["addresses"])))
                self.assertTrue(all(isinstance(s, str) and len(s) == 7 and
                                    s.startswith("0x") for s in profile["addresses"]))
            expected = old["both_original_and_native"]
            for field, key in (("menu", "menu"), ("track", "course"),
                               ("race_flag", "race_flag")):
                self.assertEqual(row["original_" + field], expected[key])
                self.assertEqual(row["native_" + field], expected[key])

    def test_six_byte_mismatches_move_and_no_address_is_persistent_all_eight(self):
        sets = [set(r["differing_byte_offsets_by_memory_class"]["wram"]["addresses"])
                for r in self.rows]
        self.assertEqual([len(s) for s in sets], [6, 6, 50, 14, 6, 6, 22, 16])
        self.assertEqual(sets[0] & sets[1], {"0x001E3"})
        self.assertEqual(sets[4], sets[5])
        self.assertFalse(set.intersection(*sets))
        self.assertEqual(self.phase["persistent_differing_wram_offsets"], [])
        self.assertEqual(len(set.union(*sets)), 57)
        self.assertFalse(self.phase["all_samples_exact_guest_bytes"])

    def test_pinned_wram_symbols_are_tentative_and_mapper_consumes_real_capture(self):
        symbols = annotator.parse_ram_symbols(annotator.RAM_SYMBOLS.read_text())
        mapped = annotator.annotate(self.phase, symbols)
        self.assertEqual(mapped["release_complete_event_credit"], 0)
        self.assertFalse(mapped["any_incomplete_address_profile"])
        self.assertEqual(len(mapped["frames"]), 8)
        labels = {
            entry["snes_wram"]: [x["name"] for x in entry["most_specific_containing_symbols"]]
            for row in mapped["frames"] for entry in row["mapped_addresses"]
        }
        self.assertIn("wJoy1Held", labels["7E:0072"])
        self.assertIn("wMenuIdleTimer", labels["7E:0089"])
        self.assertIn("wMenuAnimFrames", labels["7E:0187"])
        self.assertIn("wOamBuffer", labels["7E:0B82"])
        self.assertEqual(labels["7E:01D8"], [])
        self.assertEqual(mapped["confidence"], "tentative reverse-engineered symbol labels only")


if __name__ == "__main__":
    unittest.main()
