"""QA-01: cross-event *observed* WRAM offset overlap, no guest/result admission.

Only compare independently archived address lists and pinned tentative RAM names.
This test never asserts physics or timing equivalence from sparse snapshots.
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import annotate_bowl_guest_memory_offsets as symbols

SWITCHER_DOC = ROOT / "docs/QA01-SWITCHER-5782-RAW-MEMORY-EVIDENCE-20261010.md"
SWITCHER_WITNESS = ROOT / (
    "analysis/data/switcher-original-baldosa-same-host-5782-executed-20261010.json"
)
SWITCHER_RESTORE = ROOT / (
    "analysis/data/switcher-original-native-restoration-same-host-20261010.json"
)
BOWL_WITNESS = ROOT / (
    "analysis/data/bowl-original-native-observed-tally-wram-offsets-20261010.json"
)

# Recorded cross-event intersections to protect against accidental evidence edits.
# These are factual sample-address memberships, NOT presumed CPU owners.
EXPECTED_BOWL_HOSTS = {
    "0x001DD": (4333, 4343, 4344, 4345, 4346, 4347),
    "0x001E6": (4343, 4344, 4347),
    "0x001E7": (4343, 4344, 4347),
    "0x001EF": (4343,),
    "0x001F0": (4343, 4347),
    "0x001F1": (),
    "0x001F2": (),
    "0x001F3": (4348,),
}


class OriginalNativeEventOffsetCrosscheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        doc = SWITCHER_DOC.read_text(encoding="utf-8")
        rows = re.findall(
            r"^WRAM different-byte offsets[^\n]*:\s*(.*)$",
            doc,
            re.MULTILINE,
        )
        if len(rows) != 1:
            raise AssertionError("need one archived Switcher full-memory address row")
        cls.switcher = re.findall(r"0x[0-9A-Fa-f]{5}", rows[0])
        cls.switcher_witness = json.loads(SWITCHER_WITNESS.read_text())
        cls.restore = json.loads(SWITCHER_RESTORE.read_text())
        cls.bowl = json.loads(BOWL_WITNESS.read_text())
        cls.phase = cls.bowl["tally_anchored_guest_phase"]
        cls.samples = cls.phase["same_host_frame_samples"]

    def test_switcher_offsets_are_original_native_full_memory_observation(self):
        self.assertEqual(set(self.switcher), set(EXPECTED_BOWL_HOSTS))
        self.assertEqual(len(self.switcher), 8)
        self.assertEqual(self.switcher_witness["provenance"]["workflow_run_id"], 38076629158)
        state = self.switcher_witness["genuine_penultimate_host_capture"]
        self.assertEqual(state["reference_absolute_host"], 5782)
        self.assertEqual(state["native_absolute_host"], 5782)
        self.assertTrue(state["all_named_fields_equal"])
        self.assertEqual(state["guest_wram_bytes_read_per_engine"], 131072)
        self.assertFalse(state["original_movie_input_modified"])
        self.assertEqual(self.switcher_witness["scope_limits"]["release_complete_event_credit"], 0)

    def test_completed_restoration_is_not_requested_again(self):
        observed = self.restore["observed"]
        restoration = observed["restore_transition"]
        self.assertEqual(restoration["reference_first_restored_host"], 5778)
        self.assertEqual(restoration["native_first_restored_host"], 5778)
        self.assertEqual(
            restoration["reference_native_same_absolute_host_frames_with_all_sampled_fields_identical"],
            [5778, 5779, 5780],
        )
        self.assertEqual(observed["original_result_host"], 5783)
        self.assertEqual(observed["native_result_host"], 5783)
        self.assertFalse(self.restore["acceptance"]["guest_relative_terminal_matched"])
        self.assertEqual(self.restore["acceptance"]["release_usa_courses_accepted"], 0)

    def test_bowl_overlap_is_exact_and_all_eight_offset_profiles_complete(self):
        self.assertEqual(self.bowl["provenance"]["workflow_run_id"], 38025090532)
        self.assertEqual(self.phase["reference_and_native_tally_host_frame"], 4279)
        self.assertEqual(self.phase["reference_and_native_result_host_frame"], 4349)
        self.assertEqual(len(self.samples), 8)
        self.assertEqual(self.phase["offset_profile_cap_per_memory_class"], 128)
        self.assertFalse(self.phase["retains_raw_guest_memory"])
        frames_for_address = {offset: [] for offset in self.switcher}
        all_bowl = set()
        for row in self.samples:
            self.assertEqual(
                row["absolute_host_frame"],
                4279 + row["offset_from_actual_tally_host_frame"],
            )
            profile = row["differing_byte_offsets_by_memory_class"]["wram"]
            self.assertIs(profile["truncated"], False)
            self.assertEqual(profile["total"], row["different_guest_bytes"]["wram"])
            self.assertEqual(len(profile["addresses"]), profile["total"])
            self.assertEqual(profile["addresses"], sorted(set(profile["addresses"])))
            all_bowl.update(profile["addresses"])
            for address in frames_for_address:
                if address in profile["addresses"]:
                    frames_for_address[address].append(row["absolute_host_frame"])
        self.assertEqual(len(all_bowl), 57)
        for offset, expected in EXPECTED_BOWL_HOSTS.items():
            with self.subTest(offset=offset):
                self.assertEqual(tuple(frames_for_address[offset]), expected)
        self.assertEqual(sum(offset in all_bowl for offset in self.switcher), 6)
        self.assertEqual(self.phase["release_complete_event_credit"], 0)

    def test_eight_switcher_offsets_have_no_pinned_ram_name(self):
        catalog = symbols.parse_ram_symbols(symbols.RAM_SYMBOLS.read_text())
        for address in self.switcher:
            with self.subTest(address=address):
                mapping = symbols.lookup(int(address, 16), catalog)
                self.assertEqual(mapping["most_specific_containing_symbols"], [])
                self.assertEqual(mapping["exact_start_symbols"], [])
                self.assertTrue(mapping["snes_wram"].startswith("7E:"))
                self.assertIn("source labels", mapping["interpretation"])


if __name__ == "__main__":
    unittest.main()
