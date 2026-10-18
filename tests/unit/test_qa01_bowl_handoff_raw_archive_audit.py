"""ROM-free negative tests for independent Bowl raw archive acceptance audit."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_bowl_handoff_raw_archive_audit as audit


class RawBowlArchiveTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "bowl" / "replay" / "ref").mkdir(parents=True)
        (self.root / "bowl" / "replay" / "native").mkdir(parents=True)

    def make(self, native_mismatch: bool = False):
        movie_samples = {}
        rows = []
        logs = {"reference": [], "native": []}
        original_host, native_host = 984, 984
        original_result, native_result = 3365, 3365
        sram = bytearray(8192)
        sram[0x0426:0x0428] = (764).to_bytes(2, "little")
        sram[0x054E:0x0550] = (764).to_bytes(2, "little")
        for offset in audit.OFFSETS:
            active = offset >= 342
            state = {"menu": 0 if active else 0x16,
                     "track": 3 if active else 2,
                     "in_race": 1 if active else 0}
            movie = {"original_movie_host_frame": audit.SOURCE_RESULT + offset, **state}
            movie_samples[str(offset)] = movie
            guests, ram = {}, {}
            for side, folder, logname, entry, result in (
                ("original", "ref", "reference", original_host, original_result),
                ("native", "native", "native", native_host, native_result),
            ):
                tag = f"bowl-next-switcher-{offset:03d}"
                memory = bytearray(131072)
                memory[0x9F], memory[0xCE], memory[0x313] = (
                    state["menu"], state["track"], state["in_race"])
                if native_mismatch and side == "native" and offset == 342:
                    memory[0x01DD] = 0x40
                path = self.root / "bowl" / "replay" / folder
                (path / f"{tag}.wram.bin").write_bytes(memory)
                (path / f"{tag}.sram.bin").write_bytes(sram)
                ram[side] = bytes(memory)
                host = entry + result + offset
                logs[logname].append(f"script f={host} dump {tag} ok")
                rank, good = audit.bowl_rank0(bytes(sram))
                guests[side] = {
                    "actual_host_frame": host, **state,
                    "full_wram_bytes": 131072, "wram_sha256": audit.digest(memory),
                    "full_sram_bytes": 8192, "sram_sha256": audit.digest(sram),
                    "source_earned_bowl_rank0": rank,
                    "record_table_checksum_matches": good}
            cmp = audit.raw_wram_pair(ram["original"], ram["native"])
            rows.append({
                "offset_from_observed_bowl_result": offset,
                "original_movie": movie,
                "fresh_guests": guests,
                "triplet_named_states_equal": True,
                "full_sram_pair_equal": True,
                "full_wram_byte_difference": cmp,
            })
        for name, lines in logs.items():
            (self.root / "bowl" / "replay" / (name + ".log")).write_text(
                "\n".join(lines) + "\n", encoding="utf-8")
        brackets = {name: audit.bracket(rows, name)
                    for name in ("movie", "original", "native")}
        handoff = {
            "schema": audit.PRODUCER_SCHEMA,
            "source_original_result_frame": 11985,
            "source_original_next_switcher_frame": 12327,
            "source_next_switcher_entry_offset": 342,
            "original_movie_entry_bracket": brackets["movie"],
            "fresh_reference_entry_bracket": brackets["original"],
            "fresh_native_entry_bracket": brackets["native"],
            "fresh_reference_entry_offset": 342,
            "fresh_native_entry_offset": 342,
            "fresh_reference_entry_absolute_host_frame": 4691,
            "fresh_native_entry_absolute_host_frame": 4691,
            "same_absolute_host_entry": True,
            "all_three_entry_offsets_equal": True,
            "all_triplet_named_states_equal": True,
            "all_full_8192_sram_pairs_equal": True,
            "all_full_128k_wram_pairs_equal": not native_mismatch,
            "full_wram_differing_sample_offsets": [342] if native_mismatch else [],
            "source_earned_bowl_rank0_764_and_checksum_every_sample": True,
            "sample_offsets": list(audit.OFFSETS),
            "samples": rows,
            "source_controller_masks_modified": False,
            "original_native_clocks_unrebased": True,
            "full_cpu_spc_logic_tick_equivalence_proven": False,
            "shipping_windows_candidate_proven": False,
            "cold_process_disk_persistence_proven": False,
            "release_complete_event_credit": 0,
        }
        original_source = {
            "original_entry_frame": 8620,
            "original_result_frame": 11985,
            "source_active_frames_to_result": 3365,
            "source_next_switcher": {
                "source_result_host_frame": 11985,
                "source_next_switcher_entry_host_frame": 12327,
                "source_result_to_next_active_entry_frames": 342,
                "source_active_eight_consecutive_frames": True,
                "source_controller_masks_modified": False,
                "release_complete_event_credit": 0,
                "samples": movie_samples,
            },
        }
        report = {
            "schema_version": 1,
            "name": "bowl", "course_id": "course:03", "family": "stunt",
            "native_backend": "pinned-baldosa",
            "admission": "investigative candidate; not a release-ledger pass",
            **{key: "a" * 64 for key in (
                "rom_sha256", "original_movie_sha256", "source_sram_sha256",
                "input_sha256", "native_executable_sha256", "reference_core_sha256",
                "reference_script_sha256", "original_movie_window_sha256")},
            "reference_entry": original_host, "native_entry": native_host,
            "native_frame_shift": native_host - original_host,
            "original_source_event": original_source,
            "comparison": {
                "paired_event_candidate": True,
                "terminal_result_frame_matched": True,
                "terminal_result_guest_frame": {
                    "reference_relative": original_result,
                    "native_relative": native_result,
                }},
            "bowl_next_switcher_handoff": handoff,
        }
        self.write_report(report)
        return report

    def write_report(self, report):
        (self.root / "bowl-report.json").write_text(
            json.dumps(report, sort_keys=True) + "\n", encoding="utf-8")

    def test_complete_exact_raw_archive_is_bounded_and_never_admitted(self):
        self.make()
        result = audit.audit(self.root)
        self.assertEqual(result["observed_raw_wram_sram_pairs"], 12)
        self.assertEqual(result["raw_unmasked_wram_differing_byte_occurrences"], 0)
        self.assertEqual(result["bounded_outcome"],
                         "all_sampled_requirements_satisfied_not_admission")
        self.assertEqual(result["independent_complete_usa_event_adjudication"], "HOLD")
        self.assertEqual(result["accepted_event_credit"], 0)
        self.assertFalse(result["source_eight_frame_continuity_rechecked_from_raw"])

    def test_real_byte_divergence_reported_without_invalidating_evidence(self):
        self.make(native_mismatch=True)
        result = audit.audit(self.root)
        self.assertEqual(result["raw_unmasked_wram_differing_sample_offsets"], [342])
        self.assertEqual(result["raw_unmasked_wram_differing_byte_occurrences"], 1)
        self.assertEqual(result["bounded_outcome"],
                         "verified_bounded_difference_or_missing_lifecycle")
        self.assertEqual(result["accepted_event_credit"], 0)

    def test_missing_or_wrong_raw_data_is_invalid_evidence_not_a_game_result(self):
        self.make()
        native = self.root / "bowl" / "replay" / "native"
        target = native / "bowl-next-switcher-342.wram.bin"
        target.unlink()
        with self.assertRaisesRegex(ValueError, "missing/symlinked"):
            audit.audit(self.root)
        self.make()
        target.write_bytes(b"short")
        with self.assertRaisesRegex(ValueError, "short or oversized"):
            audit.audit(self.root)
        self.make()
        sram = native / "bowl-next-switcher-342.sram.bin"
        changed = bytearray(sram.read_bytes())
        changed[0x10A7] = 19
        sram.write_bytes(changed)
        with self.assertRaisesRegex(ValueError, "authentic raw WRAM/SRAM differs"):
            audit.audit(self.root)

    def test_detect_claimed_result_or_byte_count_forgery(self):
        report = self.make(native_mismatch=True)
        report = copy.deepcopy(report)
        row = next(x for x in report["bowl_next_switcher_handoff"]["samples"]
                   if x["offset_from_observed_bowl_result"] == 342)
        row["full_wram_byte_difference"]["differing_byte_count"] = 0
        self.write_report(report)
        with self.assertRaisesRegex(ValueError, "byte census"):
            audit.audit(self.root)
        report = self.make(native_mismatch=True)
        report["bowl_next_switcher_handoff"]["all_full_128k_wram_pairs_equal"] = True
        self.write_report(report)
        with self.assertRaisesRegex(ValueError, "aggregate contradicted"):
            audit.audit(self.root)

    def test_guest_clock_and_source_registration_fail_closed(self):
        report = self.make()
        report["bowl_next_switcher_handoff"]["samples"][5]["original_movie"][
            "original_movie_host_frame"] += 1
        self.write_report(report)
        with self.assertRaisesRegex(ValueError, "original source frame"):
            audit.audit(self.root)
        self.make()
        log = self.root / "bowl" / "replay" / "reference.log"
        log.write_text(log.read_text().replace(
            "script f=4691 dump bowl-next-switcher-342",
            "script f=4693 dump bowl-next-switcher-342"))
        with self.assertRaisesRegex(ValueError, "guest frame receipt"):
            audit.audit(self.root)

    def test_promotional_or_cross_source_receipt_is_invalid(self):
        report = self.make()
        report["bowl_next_switcher_handoff"]["release_complete_event_credit"] = 1
        self.write_report(report)
        with self.assertRaisesRegex(ValueError, "over-promotional"):
            audit.audit(self.root)
        report = self.make()
        report["rom_sha256"] = "not-a-digest"
        self.write_report(report)
        with self.assertRaisesRegex(ValueError, "immutable input"):
            audit.audit(self.root)


if __name__ == "__main__":
    unittest.main()
