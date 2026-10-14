"""QA-01: independently archived Bowl scored tally/latch report regressions.

All positive runtime facts come from *two already executed* source artifacts.
Synthetic tampering below is adversarial validation, never a new guest replay.
"""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_bowl_tally_latch_crosswalk as cross
import annotate_bowl_guest_memory_offsets as symbols


class BowlHeldLatchCrosswalkTests(unittest.TestCase):
    def setUp(self):
        self.offsets = json.loads(cross.OFFSETS.read_text())
        self.counts = json.loads(cross.COUNTS.read_text())

    def test_crosscheck_two_independent_real_archived_runs(self):
        result = cross.crosswalk(self.offsets, self.counts)
        self.assertEqual(result["schema"], cross.SCHEMA)
        self.assertEqual(result["provenance"], {
            "offset_capture_run": 38025090532,
            "offset_capture_artifact": 11659973901,
            "independent_count_run": 38024468581,
            "independent_count_artifact": 11659683037,
        })
        self.assertEqual(result["original_native_same_absolute_host_tally"], 4279)
        self.assertEqual(result["original_native_same_absolute_host_result"], 4349)
        self.assertEqual(result["real_scored_stunt"], 764)
        self.assertEqual([f["absolute_host"] for f in result["frames"]],
                         [4333, 4339, 4343, 4344, 4345, 4346, 4347, 4348])
        self.assertEqual([f["different_guest_bytes"]["wram"]
                          for f in result["frames"]], [6, 6, 50, 14, 6, 6, 22, 16])
        self.assertTrue(result["earlier_two_samples_only_unattributed_stack_page_offsets"])
        self.assertTrue(result["same_six_unattributed_stack_page_offsets_at_4345_and_4346"])
        self.assertFalse(result["original_native_controller_masks_consumed_equal_proven"])
        self.assertFalse(result["original_native_guest_cpu_nmi_phase_equivalent_proven"])
        self.assertFalse(result["source_original_writer_or_consumer_pc_identified"])
        self.assertFalse(result["strict_complete_event_accepted"])
        self.assertEqual(result["release_credit"], 0)

    def test_earliest_named_latch_disagreement_is_high_byte_at_4343_not_4347(self):
        r = cross.crosswalk(self.offsets, self.counts)
        self.assertEqual(r["first_observed_changed_joy1_held_word_host"], 4343)
        self.assertEqual(r["first_observed_named_or_oam_region_host"], 4343)
        at = {row["absolute_host"]: row for row in r["frames"]}
        self.assertEqual(
            [(f, at[f]["named_joypad_word_different_low"],
              at[f]["named_joypad_word_different_high"])
             for f in (4343, 4347, 4348)],
            [(4343, False, True), (4347, True, True), (4348, True, False)])
        self.assertEqual(at[4343]["wram_regions"]["joy1_held_word_bytes"],
                         ["0x00073"])
        self.assertEqual(at[4343]["wram_regions"]["menu_timing_bytes"],
                         ["0x00089", "0x0008B"])
        self.assertEqual(len(at[4343]["wram_regions"]["named_menu_animation_frames"]), 8)
        self.assertEqual(at[4343]["wram_regions"]["named_menu_animation_phase"],
                         ["0x00191"])
        self.assertEqual(at[4343]["wram_regions"]["unattributed_stack_page_bytes"][-2:],
                         ["0x001EF", "0x001F0"])
        self.assertEqual(len(at[4343]["wram_regions"]["oam_shadow_region_bytes"]), 17)
        self.assertEqual(at[4343]["vram_different_offsets"],
                         ["0x0245C", "0x0249C"])
        self.assertEqual(at[4343]["cgram_different_offsets"], [])
        self.assertTrue(all(row["stage_track"] == 2 and
                            row["stage_race_flag"] == 60
                            for row in r["frames"]))

    def test_name_spans_come_from_pinned_imported_map_not_raw_stack_page_guess(self):
        m = symbols.parse_ram_symbols(symbols.RAM_SYMBOLS.read_text())
        for addr, name in ((0x72, "wJoy1Held"),
                           (0x73, "wJoy1Held"),
                           (0x89, "wMenuIdleTimer"),
                           (0x8B, "wMenuAnimTimer"),
                           (0x187, "wMenuAnimFrames"),
                           (0x18E, "wMenuAnimFrames"),
                           (0x191, "wMenuAnimPhase"),
                           (0xB82, "wOamBuffer")):
            with self.subTest(address=addr):
                obj = symbols.lookup(addr, m)
                self.assertIn(name, [
                    s["name"] for s in obj["most_specific_containing_symbols"]])
        self.assertEqual(cross.classify_address(0x192),
                         "unattributed_stack_page_bytes")
        self.assertEqual(cross.classify_address(0x1DD),
                         "unattributed_stack_page_bytes")

    def test_fail_closed_on_wrong_original_sources_or_fabricated_acceptance(self):
        for label, patch in (
            ("offset_run", lambda a, b: a["provenance"].update(
                workflow_run_id=123)),
            ("count_run", lambda a, b: b["source"].update(
                artifact_id=123)),
            ("event", lambda a, b: b["scored_stunt"].update(score=765)),
            ("claim", lambda a, b: a["tally_anchored_guest_phase"].update(
                release_complete_event_credit=1)),
            ("other_claim", lambda a, b: b.update(
                release_complete_usa_courses_credited=1)),
            ("host", lambda a, b: a["tally_anchored_guest_phase"]
                ["same_host_frame_samples"][2].update(absolute_host_frame=4344)),
            ("count", lambda a, b: b["phase_samples"][2]
                ["guest_different_bytes"].update(wram=51)),
            ("memory", lambda a, b: a["tally_anchored_guest_phase"]
                ["same_host_frame_samples"][2]["different_guest_bytes"]
                .update(vram=3)),
            ("stage", lambda a, b: a["tally_anchored_guest_phase"]
                ["same_host_frame_samples"][2].update(native_menu=132)),
        ):
            with self.subTest(label=label):
                a,b=copy.deepcopy(self.offsets),copy.deepcopy(self.counts)
                patch(a,b)
                with self.assertRaises(ValueError):
                    cross.crosswalk(a,b)

    def test_fail_closed_on_profile_truncation_or_wrong_address_order(self):
        cases = (
            lambda x: x.update(truncated=True),
            lambda x: x["addresses"].pop(),
            lambda x: x["addresses"].__setitem__(0, "0x0FFFF"),
            lambda x: x["addresses"].__setitem__(1, "0x00073"),
            lambda x: x["addresses"].__setitem__(0, "0xZZZZZ"),
        )
        for patch in cases:
            with self.subTest(case=str(patch)):
                a=copy.deepcopy(self.offsets)
                profile=a["tally_anchored_guest_phase"]["same_host_frame_samples"][2]["differing_byte_offsets_by_memory_class"]["wram"]
                patch(profile)
                with self.assertRaises(ValueError):
                    cross.crosswalk(a,self.counts)


if __name__ == "__main__":
    unittest.main()
