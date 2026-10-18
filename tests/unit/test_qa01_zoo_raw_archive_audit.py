"""Synthetic ROM-free full Zoo guest archive integrity tests. Never game proof."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_zoo_raw_archive_audit as target

OFFSETS = tuple(range(64)) + tuple(range(5034, 5047)) + (5120,)


class ZooRawArchiveAuditTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / "work" / "zoom-zoo" / "replay"
        for side in ("ref", "native"):
            (self.base / side).mkdir(parents=True)

    def write_json(self, name, obj):
        (self.root / name).write_text(
            json.dumps(obj, indent=2) + "\n", encoding="utf-8")

    def make(self, *, mesh_byte_difference=False):
        self.assertEqual(len(OFFSETS), target.CHECKPOINT_COUNT)
        original = bytes(131072)
        modified = bytearray(original)
        modified[0x01ED] = 41
        native_changed = bytes(modified)
        sram = bytearray(8192)
        sram[0x0424:0x0426] = (2510).to_bytes(2, "little")
        sram[0x054E:0x0550] = (2510).to_bytes(2, "little")
        sram = bytes(sram)
        rank = target.rank_and_checksum(sram)
        self.assertEqual(rank["value_word"], 2510)
        self.assertEqual(rank["checksum_stored"], rank["checksum_calculated"])
        logs = {"ref": [], "native": []}
        rows = []
        for off in OFFSETS:
            tag = "race-entered" if off == 0 else f"scene-{off:05d}"
            pair = {}
            for side in ("ref", "native"):
                memory = (native_changed if side == "native" and
                          off == 1 and mesh_byte_difference else original)
                (self.base / side / (tag + ".wram.bin")).write_bytes(memory)
                (self.base / side / (tag + ".sram.bin")).write_bytes(sram)
                logs[side].append(f"script f={1017 + off} dump {tag} ok")
                pair[side] = (memory, sram)
            comp = target.raw_wram_pair(pair["ref"][0], pair["native"][0])
            rows.append({
                "race_relative_frame": off,
                "original_absolute_host_frame": 1017 + off,
                "native_absolute_host_frame": 1017 + off,
                "original_native_full_wram_byte_difference": comp,
            })
        handoff = []
        for off in target.BOWL_OFFSETS:
            tag = f"zoo-next-bowl-{off:03d}"
            guests = {}
            for side, label in (("ref", "original"), ("native", "native")):
                (self.base / side / (tag + ".wram.bin")).write_bytes(original)
                (self.base / side / (tag + ".sram.bin")).write_bytes(sram)
                logs[side].append(f"script f={1017 + 5163 + off} dump {tag} ok")
                guests[label] = {
                    "actual_host_frame": 1017 + 5163 + off,
                    "full_wram_bytes": 131072,
                    "wram_sha256": target.digest(original),
                    "sram_sha256": target.digest(sram),
                    "source_earned_zoo_best_lap": {
                        k: rank[k] for k in ("rank", "value_word", "holder_index")},
                    "record_checksum_stored": rank["checksum_stored"],
                    "record_checksum_calculated": rank["checksum_calculated"],
                    "record_checksum_matches": True,
                }
            handoff.append({
                "offset_from_observed_zoo_result": off,
                "fresh_guests": guests,
                "original_native_full_wram_byte_difference":
                    target.raw_wram_pair(original, original),
                "original_native_full_sram_equal": True,
                "battery_sram_differing_byte_count": 0,
                "battery_first_differences": [],
            })
        for side, filename in (("ref", "reference.log"), ("native", "native.log")):
            (self.base / filename).write_text(
                "\n".join(logs[side]) + "\n", encoding="utf-8")
        first = next((r for r in rows if r["original_native_full_wram_byte_difference"][
            "differing_byte_count"]), None)
        first_report = None if first is None else {
            "race_relative_frame": first["race_relative_frame"],
            "original_absolute_host_frame": first["original_absolute_host_frame"],
            "native_absolute_host_frame": first["native_absolute_host_frame"],
            "first_differing_address": first[
                "original_native_full_wram_byte_difference"]["first_differing_address"],
            "differing_byte_count": first[
                "original_native_full_wram_byte_difference"]["differing_byte_count"],
        }
        dense_rows = []
        for off in range(5034, 5047):
            dense_rows.append({
                "race_relative_frame": off,
                "original_absolute_host_frame": 1017 + off,
                "native_absolute_host_frame": 1017 + off,
                "bytes": [
                    {"address": f"7E:{addr:04X}",
                     "original": 0, "native": 0, "differs": False}
                    for addr in (0x63, 0x69)],
                "full_wram_differing_bytes": 0,
            })
        for sample in handoff:
            off = sample["offset_from_observed_zoo_result"]
            sample["original_movie"] = {
                "original_movie_host_frame": 8353 + off,
                "menu": 0, "track": 0, "in_race": 0,
            }
            sample["triplet_named_states_equal"] = True
        report = {
            "name": "zoom-zoo",
            "course_id": "course:02",
            "native_backend": "pinned-baldosa",
            "reference_entry": 1017,
            "native_entry": 1017,
            "original_source_event": {
                "original_entry_frame": 3190,
                "original_result_frame": 8353,
                "source_active_frames_to_result": 5163,
            },
            "zoo_race_mesh": {
                "mesh_checkpoint_count": 78,
                "all_128k_wram_bytes_examined_per_pair": 131072,
                "masked_or_excluded_wram_bytes": 0,
                "release_complete_usa_event_credit": 0,
                "every_gameplay_frame_compared": False,
                "cpu_instruction_or_logic_tick_parity_proven": False,
                "native_os_disk_persistence_proven": False,
                "original_2014_source_controller_masks_modified": False,
                "raw_byte_exact_sample_count": 77 if mesh_byte_difference else 78,
                "first_nonidentical_raw_wram_pair": first_report,
                "late_direct_page_window": {
                    "range_inclusive": [5034, 5046],
                    "all_guest_frames_in_range_captured": True,
                    "raw_wram_bytes_excluded": 0,
                    "release_complete_event_credit": 0,
                    "samples": dense_rows,
                    "first_sampled_direct_page_disagreement": None,
                    "last_sampled_direct_page_disagreement": None,
                },
                "samples": rows,
            },
            "zoo_next_bowl_handoff": {
                "sample_offsets": list(target.BOWL_OFFSETS),
                "sample_count": len(target.BOWL_OFFSETS),
                "release_complete_event_credit": 0,
                "source_controller_masks_modified": False,
                "full_event_guest_logic_tick_equivalence_proven": False,
                "shipping_windows_candidate_proven": False,
                "cold_process_disk_persistence_proven": False,
                "all_original_native_full_sram_pairs_equal": True,
                "all_original_native_full_wram_pairs_equal": True,
                "all_triplet_named_states_equal": True,
                "zoo_rank0_2510_and_checksum_preserved_every_sample": True,
                "fresh_reference_next_bowl_entry_offset": None,
                "fresh_native_next_bowl_entry_offset": None,
                "samples": handoff,
            },
        }
        self.save_report(report)
        return report

    def save_report(self, report):
        self.write_json("producer-report.json", report)
        sha = hashlib.sha256((self.root / "producer-report.json").read_bytes()).hexdigest()
        self.write_json("case-result.json", {
            "case": "zoom-zoo",
            "course_id": "course:02",
            "evidence": {"producer_sha256": sha},
            "release_credit": 0,
            "disposition": "strict_candidate",
        })

    def test_full_exact_78_plus_11_synthetic_audit_never_admits_event(self):
        self.make()
        result = target.audit(self.root)
        self.assertEqual(result["full_zoo_mesh_rehashed_original_native_128k_pairs"], 78)
        self.assertEqual(result["full_zoo_mesh_exact_pairs"], 78)
        self.assertEqual(result["next_bowl_full_wram_and_sram_pairs_rehashed"], 11)
        self.assertEqual(result["next_bowl_sram_unequal_offsets"], [])
        self.assertEqual(result["independent_usa_event_adjudication"], "HOLD")
        self.assertEqual(result["accepted_usa_events"], 0)

    def test_real_byte_disagreement_remains_negative_without_masking(self):
        self.make(mesh_byte_difference=True)
        result = target.audit(self.root)
        self.assertEqual(result["full_zoo_mesh_exact_pairs"], 77)
        self.assertEqual(result["full_zoo_mesh_unmasked_differing_byte_occurrences"], 1)
        self.assertEqual(result["full_zoo_mesh_reported_difference_address_occurrences"],
                         {"7E:01ED": 1})
        self.assertEqual(result["accepted_usa_events"], 0)

    def test_missing_short_tampered_guest_files_reject_false_proof(self):
        self.make()
        path = self.base / "native" / "scene-00001.wram.bin"
        value = bytearray(path.read_bytes())
        value[0x01ED] = 22
        path.write_bytes(value)
        with self.assertRaisesRegex(ValueError, "contradicts producer"):
            target.audit(self.root)
        self.make()
        path = self.base / "native" / "zoo-next-bowl-267.sram.bin"
        path.write_bytes(bytes(8191))
        with self.assertRaisesRegex(ValueError, "short or oversized"):
            target.audit(self.root)

    def test_forged_report_or_original_guest_clock_invalid(self):
        report = self.make()
        report["zoo_race_mesh"]["raw_byte_exact_sample_count"] = 77
        self.save_report(report)
        with self.assertRaisesRegex(ValueError, "exact checkpoints"):
            target.audit(self.root)
        self.make()
        path = self.base / "reference.log"
        path.write_text(path.read_text().replace(
            "script f=1018 dump scene-00001",
            "script f=1020 dump scene-00001"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "host clock"):
            target.audit(self.root)

    def test_forged_dense_sound_pointer_and_earned_bowl_claims_rejected(self):
        report = self.make()
        report["zoo_race_mesh"]["late_direct_page_window"]["samples"][6]["bytes"][0][
            "original"] = 1
        self.save_report(report)
        with self.assertRaisesRegex(ValueError, "dense 13-frame"):
            target.audit(self.root)
        report = self.make()
        report["zoo_next_bowl_handoff"][
            "zoo_rank0_2510_and_checksum_preserved_every_sample"] = False
        self.save_report(report)
        with self.assertRaisesRegex(ValueError, "earned record"):
            target.audit(self.root)

    def test_cannot_promote_sampled_bytes_to_unobserved_cpu_or_disk_proof(self):
        report = self.make()
        report["zoo_race_mesh"]["cpu_instruction_or_logic_tick_parity_proven"] = True
        self.save_report(report)
        with self.assertRaisesRegex(ValueError, "falsely promoted proof"):
            target.audit(self.root)
        report = self.make()
        report["zoo_next_bowl_handoff"]["shipping_windows_candidate_proven"] = True
        self.save_report(report)
        with self.assertRaisesRegex(ValueError, "next Bowl proof absent"):
            target.audit(self.root)

    def test_legitimate_strict_divergence_still_gets_raw_byte_audit(self):
        self.make(mesh_byte_difference=True)
        classification = json.loads((self.root / "case-result.json").read_text())
        classification["disposition"] = "strict_divergence"
        self.write_json("case-result.json", classification)
        result = target.audit(self.root)
        self.assertEqual(result["full_zoo_mesh_unmasked_differing_byte_occurrences"], 1)
        self.assertEqual(result["independent_usa_event_adjudication"], "HOLD")

    def test_rank_checksum_uses_complete_original_150_word_table(self):
        battery = bytearray(8192)
        battery[0x0424:0x0426] = (2510).to_bytes(2, "little")
        battery[0x054E:0x0550] = (2510).to_bytes(2, "little")
        rank = target.rank_and_checksum(battery)
        self.assertEqual(rank["value_word"], 2510)
        self.assertEqual(rank["checksum_stored"], rank["checksum_calculated"])
        battery[0x0422] = 1
        self.assertNotEqual(target.rank_and_checksum(battery)["checksum_stored"],
                            target.rank_and_checksum(battery)["checksum_calculated"])
        with self.assertRaisesRegex(ValueError, "8192-byte"):
            target.rank_and_checksum(bytes(8191))


if __name__ == "__main__":
    unittest.main()
