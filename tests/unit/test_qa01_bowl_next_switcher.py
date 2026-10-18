"""Synthetic Bowl -> Switcher clock, source and raw-memory guards; no game pass."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_original_event_complete as producer
import qa01_bowl_switcher_handoff as target


class BowlNextSwitcherTests(unittest.TestCase):
    def setUp(self):
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        self.ref = Path(root.name) / "ref"
        self.native = Path(root.name) / "native"
        self.ref.mkdir()
        self.native.mkdir()
        self.states = {}
        for offset in target.OFFSETS:
            frame = target.SOURCE_BOWL_RESULT + offset
            self.states[frame] = {
                "menu": 0 if offset >= 342 else 0x16,
                "track": 3,
                "in_race": 1 if offset >= 342 else 0,
            }
        for frame in range(target.SOURCE_SWITCHER_ENTRY, target.SOURCE_SWITCHER_ENTRY + 8):
            self.states[frame] = {"menu": 0, "track": 3, "in_race": 1}
        self.states[target.SOURCE_SWITCHER_ENTRY - 1] = {
            "menu": 0x16, "track": 3, "in_race": 0}
        self.proof = target.source_next_switcher(self.states, 11985)
        self.ref_log, self.native_log = self._write()

    def _write(self, early=None):
        logs = []
        for side, directory, entry, result in (
                ("original", self.ref, 984, 3365),
                ("native", self.native, 985, 3364)):
            lines = []
            for offset in target.OFFSETS:
                tag = f"bowl-next-switcher-{offset:03d}"
                state = dict(self.proof["samples"][str(offset)])
                if side == "native" and early is not None and offset >= early:
                    state["in_race"] = 1
                    state["menu"] = 0
                wram = bytearray(0x20000)
                wram[0x009F] = state["menu"]
                wram[0x00CE] = state["track"]
                wram[0x0313] = state["in_race"]
                (directory / f"{tag}.wram.bin").write_bytes(wram)
                sram = bytearray(8192)
                # Crawler course index 2, rank 0, earned Bowl 764.
                sram[0x0426:0x0428] = (764).to_bytes(2, "little")
                sram[0x054E:0x0550] = (764).to_bytes(2, "little")
                (directory / f"{tag}.sram.bin").write_bytes(sram)
                lines.append(f"script f={entry + result + offset} dump {tag} ok")
            logs.append("\n".join(lines) + "\n")
        return logs

    def observe(self, original_log=None, native_log=None, source=None):
        return target.observe_next_switcher(
            self.ref, self.native, original_log or self.ref_log,
            native_log or self.native_log,
            self.proof if source is None else source, 984, 985, 3365, 3364,
            observed_dump_frame=producer.observed_dump_frame,
            decode_sram=producer.decode_qa01_crawler_battery_sram,
            audit_wram=producer.audit_qa01_wram_pair)

    def test_exact_2014_source_bracket_and_real_eight_frame_requirement(self):
        self.assertEqual(self.proof["source_result_to_next_active_entry_frames"], 342)
        self.assertEqual(self.proof["source_next_switcher_entry_host_frame"], 12327)
        self.assertTrue(self.proof["source_active_eight_consecutive_frames"])
        self.assertEqual(self.proof["release_complete_event_credit"], 0)
        with self.assertRaisesRegex(target.BowlSwitcherEvidenceError, "wrong original"):
            target.source_next_switcher(self.states, 11984)
        states = dict(self.states)
        states[12326] = {"menu": 0, "track": 3, "in_race": 1}
        with self.assertRaisesRegex(target.BowlSwitcherEvidenceError, "pre-entry"):
            target.source_next_switcher(states, 11985)
        states = dict(self.states)
        del states[12329]
        with self.assertRaisesRegex(target.BowlSwitcherEvidenceError, "eight actual"):
            target.source_next_switcher(states, 11985)

    def test_bowl_route_is_gated_and_controller_masks_are_unchanged(self):
        frames = producer.sample_frames("bowl", 3365)
        basic = producer.replay_script(
            3, 0x18, frames, True, source_followthrough=True)
        extended = producer.replay_script(
            3, 0x18, frames, True, source_followthrough=True,
            bowl_next_switcher=True)
        self.assertIn("dump original-follow-72\nwait 262\ndump bowl-next-switcher-334", extended)
        self.assertTrue(extended.endswith("dump bowl-next-switcher-354\nquit\n"))
        self.assertEqual(
            [line for line in basic.splitlines() if line.startswith("press ")],
            [line for line in extended.splitlines() if line.startswith("press ")])
        self.assertNotIn("poke ", extended)
        with self.assertRaisesRegex(producer.CompleteEventError, "requires"):
            producer.replay_script(3, 0x18, frames, True, bowl_next_switcher=True)
        with self.assertRaisesRegex(producer.CompleteEventError, "requires"):
            producer.replay_script(2, 0xBC, frames, False,
                                   source_followthrough=True, bowl_next_switcher=True)

    def test_three_real_host_axes_full_memory_and_record_no_admission(self):
        result = self.observe()
        self.assertEqual(result["schema"], target.SCHEMA)
        self.assertEqual(result["source_next_switcher_entry_offset"], 342)
        self.assertEqual(result["fresh_reference_entry_offset"], 342)
        self.assertEqual(result["fresh_native_entry_offset"], 342)
        self.assertTrue(result["all_three_entry_offsets_equal"])
        self.assertTrue(result["all_triplet_named_states_equal"])
        self.assertTrue(result["all_full_8192_sram_pairs_equal"])
        self.assertTrue(result["all_full_128k_wram_pairs_equal"])
        self.assertTrue(result["source_earned_bowl_rank0_764_and_checksum_every_sample"])
        self.assertEqual(result["fresh_reference_entry_absolute_host_frame"], 4691)
        self.assertEqual(result["fresh_native_entry_absolute_host_frame"], 4691)
        self.assertTrue(result["same_absolute_host_entry"])
        self.assertEqual(len(result["samples"]), len(target.OFFSETS))
        self.assertFalse(result["full_cpu_spc_logic_tick_equivalence_proven"])
        self.assertFalse(result["shipping_windows_candidate_proven"])
        self.assertFalse(result["cold_process_disk_persistence_proven"])
        self.assertEqual(result["release_complete_event_credit"], 0)

    def test_early_native_entry_is_exposed_without_shifting_inputs(self):
        self.ref_log, self.native_log = self._write(early=341)
        result = self.observe()
        self.assertEqual(result["fresh_native_entry_offset"], 341)
        self.assertEqual(result["fresh_reference_entry_offset"], 342)
        self.assertFalse(result["all_three_entry_offsets_equal"])
        self.assertFalse(result["all_triplet_named_states_equal"])
        self.assertFalse(result["same_absolute_host_entry"])
        self.assertEqual(result["release_complete_event_credit"], 0)

    def test_unmasked_stack_byte_and_unrelated_sram_byte_cannot_disappear(self):
        tag = "bowl-next-switcher-342"
        path = self.native / f"{tag}.wram.bin"
        wram = bytearray(path.read_bytes())
        wram[0x01DD] = 0x40
        path.write_bytes(wram)
        path = self.native / f"{tag}.sram.bin"
        sram = bytearray(path.read_bytes())
        sram[0x10A7] = 11
        path.write_bytes(sram)
        result = self.observe()
        row = next(x for x in result["samples"]
                   if x["offset_from_observed_bowl_result"] == 342)
        self.assertFalse(row["full_wram_byte_difference"]["byte_exact"])
        self.assertEqual(row["full_wram_byte_difference"]["differing_byte_count"], 1)
        self.assertEqual(row["full_wram_byte_difference"]["excluded_byte_count"], 0)
        self.assertFalse(row["full_sram_pair_equal"])
        self.assertEqual(result["full_wram_differing_sample_offsets"], [342])
        self.assertFalse(result["all_full_8192_sram_pairs_equal"])
        self.assertEqual(result["release_complete_event_credit"], 0)

    def test_first_named_sram_divergence_and_offset_receipts_are_independent(self):
        path = self.native / "bowl-next-switcher-340.wram.bin"
        wram = bytearray(path.read_bytes())
        wram[0x1199] = 1
        path.write_bytes(wram)
        path = self.native / "bowl-next-switcher-343.sram.bin"
        sram = bytearray(path.read_bytes())
        sram[0x10A7] = 13
        path.write_bytes(sram)
        result = self.observe()
        self.assertEqual(result["first_original_native_named_divergence_offset"], 340)
        self.assertEqual(result["first_full_sram_differing_sample_offset"], 343)
        self.assertEqual(result["full_sram_differing_sample_offsets"], [343])
        row = next(r for r in result["samples"]
                   if r["offset_from_observed_bowl_result"] == 343)
        self.assertEqual(row["full_sram_differing_byte_count"], 1)
        self.assertEqual(row["full_sram_first_16_differences"],
                         [{"offset": 0x10A7, "original_byte": 0, "native_byte": 13}])
        self.assertEqual(result["release_complete_event_credit"], 0)

    def test_exact_new_course_resource_payload_is_reported_without_inferred_acceptance(self):
        payload = bytes(range(32))
        for directory in (self.ref, self.native):
            for offset in (342, 343, 344, 345, 346, 349, 354):
                path = directory / f"bowl-next-switcher-{offset:03d}.wram.bin"
                data = bytearray(path.read_bytes())
                data[0x10000:0x10000 + len(payload)] = payload
                # Live course stream mutates only the 0x0B/0x0C cursor bytes.
                data[0x1000B:0x1000D] = bytes((0, 255))
                path.write_bytes(data)
        kwargs = dict(
            observed_dump_frame=producer.observed_dump_frame,
            decode_sram=producer.decode_qa01_crawler_battery_sram,
            audit_wram=producer.audit_qa01_wram_pair,
            switcher_payload=payload,
            validate_course_payload=producer.is_fully_loaded_course)
        result = target.observe_next_switcher(
            self.ref, self.native, self.ref_log, self.native_log,
            self.proof, 984, 985, 3365, 3364, **kwargs)
        self.assertEqual(result["source_exact_switcher_payload_observed"],
                         {"original": True, "native": True})
        self.assertEqual(result["release_complete_event_credit"], 0)
        path = self.native / "bowl-next-switcher-349.wram.bin"
        data = bytearray(path.read_bytes())
        data[0x1001F] ^= 1
        path.write_bytes(data)
        result = target.observe_next_switcher(
            self.ref, self.native, self.ref_log, self.native_log,
            self.proof, 984, 985, 3365, 3364, **kwargs)
        row = next(r for r in result["samples"]
                   if r["offset_from_observed_bowl_result"] == 349)
        self.assertFalse(row["fresh_guests"]["native"]["source_exact_switcher_course_payload"])
        self.assertFalse(row["full_wram_byte_difference"]["byte_exact"])
        self.assertEqual(result["release_complete_event_credit"], 0)
        kwargs["switcher_payload"] = None
        with self.assertRaisesRegex(target.BowlSwitcherEvidenceError,
                                    "supplied together"):
            target.observe_next_switcher(
                self.ref, self.native, self.ref_log, self.native_log,
                self.proof, 984, 985, 3365, 3364, **kwargs)

    def test_missing_or_truncated_actual_dump_and_false_report_rejected(self):
        path = self.native / "bowl-next-switcher-342.wram.bin"
        path.write_bytes(bytes(0x20000 - 1))
        with self.assertRaisesRegex(target.BowlSwitcherEvidenceError, "truncated"):
            self.observe()
        self.ref_log, self.native_log = self._write()
        path = self.native / "bowl-next-switcher-342.sram.bin"
        path.unlink()
        with self.assertRaisesRegex(target.BowlSwitcherEvidenceError, "missing executed"):
            self.observe()
        self.ref_log, self.native_log = self._write()
        invalid_log = self.native_log.replace(
            "script f=4691 dump bowl-next-switcher-342",
            "script f=4693 dump bowl-next-switcher-342")
        with self.assertRaisesRegex(target.BowlSwitcherEvidenceError, "host-clock"):
            self.observe(native_log=invalid_log)
        forged = dict(self.proof, source_result_to_next_active_entry_frames=341)
        with self.assertRaisesRegex(target.BowlSwitcherEvidenceError, "missing exact"):
            self.observe(source=forged)


if __name__ == "__main__":
    unittest.main()
