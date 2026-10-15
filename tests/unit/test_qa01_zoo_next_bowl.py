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


if __name__ == "__main__":
    unittest.main()
