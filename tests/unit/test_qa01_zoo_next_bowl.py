"""QA-01 source-qualified next-Bowl admission negative/positive diagnostics."""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_original_event_complete as m


class ZooNextBowlTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.ref, self.nat = self.root / "ref", self.root / "native"
        self.ref.mkdir()
        self.nat.mkdir()
        self.frame = 8353
        self.source = {}
        for offset in m.ZOO_NEXT_BOWL_OFFSETS:
            active = offset >= 267
            self.source[self.frame + offset] = {
                "track": 2, "in_race": 1 if active else 0,
                "menu": 0 if active else 22}
        for frame in range(8620, 8628):
            self.source[frame] = {"track": 2, "in_race": 1, "menu": 0}
        self.source[8619] = {"track": 2, "in_race": 0, "menu": 22}
        self.source_proof = m.source_zoo_next_bowl(self.source, self.frame)
        self.ref_log, self.native_log = self.guests()

    def guests(self, mismatch_at=None):
        logs = []
        for side, base, entry in (("original", self.ref, 1017),
                                  ("native", self.nat, 1019)):
            lines = []
            for offset in m.ZOO_NEXT_BOWL_OFFSETS:
                tag = f"zoo-next-bowl-{offset:03d}"
                source = self.source_proof["samples"][str(offset)]
                vals = {k: source[k] for k in ("menu", "track", "in_race")}
                if side == "native" and offset == mismatch_at:
                    vals["track"] = 1
                w = bytearray(0x20000)
                w[0x009F] = vals["menu"]
                w[0x00CE] = vals["track"]
                w[0x0313] = vals["in_race"]
                (base / f"{tag}.wram.bin").write_bytes(w)
                r = bytearray(8192)
                r[0x0424:0x0426] = (2510).to_bytes(2, "little")
                r[0x054E:0x0550] = (2510).to_bytes(2, "little")
                (base / f"{tag}.sram.bin").write_bytes(r)
                lines.append(f"script f={entry + 5163 + offset} dump {tag} ok")
            logs.append("\n".join(lines) + "\n")
        return logs

    def observed(self, reference_log=None, native_log=None):
        return m.observe_zoo_next_bowl_handoff(
            self.ref, self.nat, reference_log or self.ref_log,
            native_log or self.native_log, self.source_proof,
            1017, 1019, 5163, 5163)

    def test_original_source_proves_sustained_next_race_at_8620(self):
        proof = self.source_proof
        self.assertEqual(proof["original_next_bowl_entry_host_frame"], 8620)
        self.assertEqual(proof["source_result_to_next_active_entry_frames"], 267)
        self.assertEqual(proof["release_complete_event_credit"], 0)
        self.assertTrue(proof["source_original_active_entry_sustained_eight_frames"])
        self.assertEqual(proof["samples"]["267"]["in_race"], 1)
        self.assertEqual(proof["samples"]["266"]["in_race"], 0)

    def test_unchanged_controller_script_extended_through_new_course(self):
        frames = m.sample_frames("zoom-zoo", 5163)
        basic = m.replay_script(2, 0xBC, frames, False, source_followthrough=True)
        extended = m.replay_script(2, 0xBC, frames, False, source_followthrough=True,
                                   zoo_next_bowl=True)
        self.assertTrue(extended.endswith("dump zoo-next-bowl-280\nquit\n"))
        self.assertIn("dump original-follow-72\nwait 187\ndump zoo-next-bowl-259", extended)
        self.assertEqual([x for x in basic.splitlines() if x.startswith("press ")],
                         [x for x in extended.splitlines() if x.startswith("press ")])
        self.assertNotIn("poke ", extended)
        with self.assertRaisesRegex(m.CompleteEventError, "requires"):
            m.replay_script(2, 0xBC, frames, False, zoo_next_bowl=True)
        with self.assertRaisesRegex(m.CompleteEventError, "requires"):
            m.replay_script(3, 0x18, frames, True, source_followthrough=True,
                            zoo_next_bowl=True)

    def test_genuine_three_clock_entries_and_records_no_release_credit(self):
        obs = self.observed()
        self.assertEqual(obs["schema"], "UR-QA01-ZOO-TO-AUTHENTIC-BOWL-NEXT-RACE/1")
        self.assertEqual(obs["sample_count"], len(m.ZOO_NEXT_BOWL_OFFSETS))
        self.assertTrue(obs["all_triplet_named_states_equal"])
        self.assertTrue(obs["all_original_native_full_sram_pairs_equal"])
        self.assertTrue(obs["zoo_rank0_2510_and_checksum_preserved_every_sample"])
        self.assertEqual(obs["source_next_bowl_active_entry_offset"], 267)
        self.assertEqual(obs["fresh_reference_next_bowl_entry_offset"], 267)
        self.assertEqual(obs["fresh_native_next_bowl_entry_offset"], 267)
        # Identical result-relative entries are NOT the same absolute
        # host frame when the two race entries differ by two host frames.
        self.assertEqual(obs["reference_next_bowl_absolute_host_frame"], 6447)
        self.assertEqual(obs["native_next_bowl_absolute_host_frame"], 6449)
        self.assertFalse(obs["next_bowl_same_absolute_host_frame"])
        self.assertTrue(obs["next_bowl_entry_triple_equal"])
        self.assertFalse(obs["shipping_windows_candidate_proven"])
        self.assertFalse(obs["cold_process_disk_persistence_proven"])
        self.assertEqual(obs["release_complete_event_credit"], 0)
        for row in obs["samples"]:
            o = row["offset_from_observed_zoo_result"]
            self.assertEqual(row["original_movie"]["original_movie_host_frame"], 8353 + o)
            self.assertEqual(row["fresh_guests"]["original"]["actual_host_frame"], 6180 + o)
            self.assertEqual(row["fresh_guests"]["native"]["actual_host_frame"], 6182 + o)

    def test_observed_native_course_divergence_is_negative_not_forgiven(self):
        self.ref_log, self.native_log = self.guests(mismatch_at=267)
        obs = self.observed()
        self.assertFalse(obs["all_triplet_named_states_equal"])
        self.assertFalse(obs["next_bowl_entry_triple_equal"])
        self.assertEqual(obs["fresh_native_next_bowl_entry_offset"], 268)
        self.assertEqual(obs["release_complete_event_credit"], 0)

    def test_native_plus265_is_same_absolute_host_6447_not_wallclock_early(self):
        # Genuine RF-015 result: native relative +265 versus original +267,
        # but source/native host entries are offset by exactly two frames.
        for offset in (265, 266):
            path = self.nat / f"zoo-next-bowl-{offset:03d}.wram.bin"
            data = bytearray(path.read_bytes())
            data[0x0313] = 1
            path.write_bytes(data)
        obs = self.observed()
        self.assertEqual(obs["fresh_reference_next_bowl_entry_offset"], 267)
        self.assertEqual(obs["fresh_native_next_bowl_entry_offset"], 265)
        self.assertEqual(obs["reference_next_bowl_absolute_host_frame"], 6447)
        self.assertEqual(obs["native_next_bowl_absolute_host_frame"], 6447)
        self.assertTrue(obs["next_bowl_same_absolute_host_frame"])
        self.assertFalse(obs["next_bowl_entry_triple_equal"])
        self.assertEqual(obs["release_complete_event_credit"], 0)

    def test_early_native_bowl_entry_is_exact_at_264_not_unknown(self):
        # Actual previous run first saw native active +265 but omitted +264.
        # This now samples every relative frame from +263 through +269.
        for offset in (264, 265, 266):
            path = self.nat / f"zoo-next-bowl-{offset:03d}.wram.bin"
            data = bytearray(path.read_bytes())
            data[0x0313] = 1
            path.write_bytes(data)
        obs = self.observed()
        self.assertEqual(obs["fresh_native_next_bowl_entry_offset"], 264)
        self.assertEqual(obs["fresh_native_entry_bracket"],
                         {"last_observed_inactive_offset": 263,
                          "first_observed_active_offset": 264,
                          "exact_observed_entry_offset": 264})
        self.assertFalse(obs["next_bowl_entry_triple_equal"])
        self.assertEqual(obs["release_complete_event_credit"], 0)

    def test_nonrecord_sram_difference_is_retained_with_exact_bytes(self):
        bad = self.nat / "zoo-next-bowl-264.sram.bin"
        raw = bytearray(bad.read_bytes())
        raw[0x10A7] = 13
        bad.write_bytes(raw)
        obs = self.observed()
        row = next(r for r in obs["samples"] if
                   r["offset_from_observed_zoo_result"] == 264)
        self.assertFalse(row["original_native_full_sram_equal"])
        self.assertEqual(row["battery_sram_differing_byte_count"], 1)
        self.assertEqual(row["battery_first_differences"],
                         [{"offset": 0x10A7, "original_byte": 0,
                           "native_byte": 13}])
        self.assertEqual(obs["release_complete_event_credit"], 0)

    def test_missing_source_or_false_movie_entry_rejected(self):
        source = dict(self.source)
        del source[8620]
        with self.assertRaisesRegex(m.CompleteEventError, "missing original"):
            m.source_zoo_next_bowl(source, self.frame)
        source = dict(self.source)
        source[8619] = {"track": 2, "in_race": 1, "menu": 0}
        with self.assertRaisesRegex(m.CompleteEventError, "actually enter"):
            m.source_zoo_next_bowl(source, self.frame)
        with self.assertRaisesRegex(m.CompleteEventError, "source frame 8353"):
            m.source_zoo_next_bowl(self.source, self.frame + 1)

    def test_guest_missing_raw_memory_bad_frame_and_sram_fail_closed(self):
        removed = self.nat / "zoo-next-bowl-267.wram.bin"
        removed.unlink()
        with self.assertRaisesRegex(m.CompleteEventError, "missing actual guest"):
            self.observed()
        self.ref_log, self.native_log = self.guests()
        badlog = self.native_log.replace(
            "script f=6449 dump zoo-next-bowl-267",
            "script f=6450 dump zoo-next-bowl-267")
        with self.assertRaisesRegex(m.CompleteEventError, "guest handoff"):
            self.observed(native_log=badlog)
        bad = self.nat / "zoo-next-bowl-280.sram.bin"
        bad.write_bytes(b"short")
        with self.assertRaisesRegex(m.CompleteEventError, "8KiB"):
            self.observed()


    def test_real_rf015_original_source_negative_receipt_remains_nonadmitting(self):
        import json
        receipt_path = (ROOT / "analysis/data" /
                        "qa01-zoo-next-bowl-rf015-exact-negative-20261015.json")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["usa_complete_course_credit"], 0)
        self.assertEqual(receipt["execution"]["case_disposition"], "strict_candidate")
        self.assertEqual(receipt["execution"]["case_release_credit"], 0)
        handoff = receipt["handoff"]
        self.assertEqual((handoff["original_movie_first_bowl_relative"],
                          handoff["fresh_original_first_bowl_relative"],
                          handoff["fresh_native_first_bowl_relative"]), (267, 267, 265))
        self.assertFalse(handoff["all_named_triplets_equal"])
        self.assertTrue(handoff["fresh_next_bowl_absolute_host_equal"])
        self.assertEqual((handoff["fresh_original_bowl_entry_absolute_host"],
                          handoff["fresh_native_bowl_entry_absolute_host"]), (6447, 6447))
        self.assertEqual((handoff["fresh_original_zoo_result_absolute_host"],
                          handoff["fresh_native_zoo_result_absolute_host"]), (6180, 6182))
        self.assertFalse(handoff["original_native_result_relative_bowl_intervals_equal"])
        self.assertFalse(handoff["all_full_sram_pairs_equal"])
        self.assertEqual(handoff["differing_battery_byte_count_each_sample"], 3)
        self.assertEqual(
            [(x["address"], x["original"], x["native"])
             for x in handoff["differing_battery_addresses"]],
            [("0x0F31", "0x1A", "0x1B"),
             ("0x0F33", "0x02", "0x04"),
             ("0x10A7", "0x0C", "0x0D")])
        self.assertFalse(receipt["scientific_limits"]["rf017_cpu_correction_included"])
        self.assertEqual(receipt["scientific_limits"]["release_course_credit"], 0)


if __name__ == "__main__":
    unittest.main()
