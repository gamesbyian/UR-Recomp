"""ROM-free corruption tests for authentic Dragster→Zoo raw-archive verifier."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_dragster_zoo_raw_archive_audit as audit
from qa01_bowl_handoff_raw_archive_audit import digest, raw_wram_pair


class DragsterZooRawAuditTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.replay = self.root / "dragster/replay"
        for d in ("ref", "native"):
            (self.replay / d).mkdir(parents=True)
        (self.root / "dragster/source").mkdir(parents=True)
        source_writes = [
            (1, 0x9F, 0), (1, 0xCE, 0), (1, 0x313, 0), (1, 0xD0, 0),
            (2874, 0x9F, 153), (2935, 0x9F, 246), (2935, 0xCE, 1),
            (3178, 0x9F, 0), (3190, 0x313, 1), (3211, 0x313, 1),
        ]
        trace = "".join(
            json.dumps({"f": f, "adr": f"0x{addr:05x}", "old": "0x00",
                        "val": f"0x{val:02x}"}, separators=(",", ":")) + "\n"
            for f, addr, val in source_writes).encode("utf8")
        (self.root / "dragster/source/trace.jsonl").write_bytes(trace)
        self.trace_sha = digest(trace)
        self.original_trace_bytes = trace
        # Synthetic fixtures cannot recreate the original 135MB source trace.
        # Override ONLY the frozen trace hash to exercise independent frame
        # reconstruction, leaving original fixed ROM/movie/core hash checks live.
        patcher = mock.patch.object(audit, "FROZEN_MOVIE_TRACE", self.trace_sha)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, path, content):
        path = self.root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content) + "\n", encoding="utf8")

    def make(self):
        (self.root / "dragster/source/trace.jsonl").write_bytes(self.original_trace_bytes)
        source_rows = {}
        rows = []
        logs = {"original": [], "native": []}
        ranked = bytearray(8192)
        ranked[0x422:0x424] = (2508).to_bytes(2, "little")
        ranked[0x54e:0x550] = (2508).to_bytes(2, "little")
        storage = bytes(ranked)
        expected_rank, valid = audit.real_dragster_record(storage)
        self.assertTrue(valid)
        observed = []
        for off in audit.OFFSETS:
            source = {"original_movie_host_frame": audit.MOVIE_RESULT + off,
                      "menu": 0, "track": 1, "in_race": int(off >= 316), "tour_row": 0}
            source_rows[str(off)] = source
            guests = {}
            states = {}
            raw = {}
            for side, folder, relative in (
                ("original", "ref", 2081),
                ("native", "native", 2079),
            ):
                host = 945 + relative + off
                memory = bytearray(131072)
                memory[0xCE] = 1
                memory[0xD0] = 0
                memory[0x313] = int(off >= (315 if side == "original" else 318))
                memory[0xC6] = 1 if side == "original" else 0
                data = bytes(memory)
                save = storage if side == "original" else storage[:-1] + b"\x01"
                tag = f"dragster-next-zoo-{off:03d}"
                path = self.replay / folder
                (path / (tag + ".wram.bin")).write_bytes(data)
                (path / (tag + ".sram.bin")).write_bytes(save)
                logs[side].append(f"script f={host} dump {tag} ok")
                ranks, good = audit.real_dragster_record(save)
                guests[side] = {
                    "host_frame": host, "menu": 0, "track": 1,
                    "in_race": memory[0x313], "tour_row": 0,
                    "true_source_zoo_payload_loaded": True,
                    "full_wram_sha256": digest(data), "full_wram_bytes": len(data),
                    "full_sram_sha256": digest(save), "full_sram_bytes": len(save),
                    "dragster_record_three_ranks": ranks,
                    "ranked_records_checksum_valid": good}
                states[side] = {k: memory[v] for k, v in audit.NAME_ADDR.items()}
                raw[side] = data
            delta = [k for k in audit.NAME_ADDR if
                     source[k] != states["original"][k] or
                     source[k] != states["native"][k]]
            rows.append({
                "offset_from_respective_dragster_result": off,
                "source_original": source, "fresh_guests": guests,
                "source_to_fresh_named_disagreements": delta,
                "full_original_native_sram_pair_equal": False,
                "unmasked_full_original_native_wram_difference":
                    raw_wram_pair(raw["original"], raw["native"]),
            })
            observed.append({"offset": off, "movie": source, **states})
        (self.replay / "reference.log").write_text(
            "\n".join(logs["original"]) + "\n", encoding="utf8")
        (self.replay / "native.log").write_text(
            "\n".join(logs["native"]) + "\n", encoding="utf8")
        proof = {
            "schema": audit.PRODUCER_SCHEMA,
            "original_dragster_entry_host_frame": 794,
            "original_dragster_result_host_frame": 2874,
            "original_zoo_active_entry_host_frame": 3190,
            "source_dragster_result_to_zoo_active_frames": 316,
            "original_zoo_eight_consecutive_active_frames": True,
            "original_movie_controller_masks_modified": False,
            "release_complete_usa_event_credit": 0,
            "sample_offsets": list(audit.OFFSETS),
            "source_samples": source_rows,
            "original_source_trace_sha256": self.trace_sha,
        }
        brackets = {who: audit.entry_bracket(observed, who)
                    for who in ("movie", "original", "native")}
        handoff = {
            "schema": audit.PRODUCER_SCHEMA,
            "original_movie_dragster_result_frame": 2874,
            "original_movie_zoo_entry_frame": 3190,
            "original_movie_zoo_entry_relative_to_dragster_result": 316,
            "entry_brackets": brackets,
            "all_three_guest_result_relative_entry_offsets_equal": False,
            "fresh_original_absolute_zoo_onset_host": 945 + 2081 + 315,
            "fresh_native_absolute_zoo_onset_host": 945 + 2079 + 318,
            "first_source_or_guest_named_mismatch_offset": 315,
            "all_full_sram_pairs_equal": False,
            "full_wram_difference_offsets": list(audit.OFFSETS),
            "fresh_original_loaded_true_zoo_course_while_active": True,
            "fresh_native_loaded_true_zoo_course_while_active": True,
            "original_native_ranked_checksum_valid_all_samples": True,
            "samples": rows,
            "source_controller_masks_rephased": False,
            "original_native_complete_dragster_cpu_spc_frame_parity_proven": False,
            "original_native_complete_zoo_event_proven": False,
            "cold_host_disk_persistence_proven": False,
            "shipping_windows_source_identity_proven": False,
            "release_complete_usa_event_credit": 0,
        }
        report = {
            "course_id": "course:01", "name": "dragster", "family": "race-a",
            "native_backend": "pinned-baldosa",
            "admission": "investigative candidate; not a release-ledger pass",
            **audit.FROZEN_SOURCE,
            "native_executable_sha256": "a" * 64,
            "reference_script_sha256": audit.FROZEN_SOURCE["input_sha256"],
            "reference_entry": 945, "native_entry": 945, "native_frame_shift": 0,
            "original_source_event": {"original_entry_frame": 794,
                                      "original_result_frame": 2874,
                                      "source_active_frames_to_result": 2080,
                                      "source_next_zoo": proof},
            "comparison": {"paired_event_candidate": False,
                           "terminal_result_frame_matched": False,
                           "bounded_dragster_to_zoo_diagnostic_without_full_event_parity": True,
                           "terminal_result_guest_frame": {
                               "reference_relative": 2081, "native_relative": 2079}},
            "dragster_next_zoo_handoff": handoff,
        }
        self.write("dragster-report.json", report)
        self.write("dragster/source/dragster-next-zoo-original.json", proof)
        return report

    def test_all_fourteen_original_native_raw_snapshots_stay_unaccepted(self):
        self.make()
        result = audit.audit(self.root)
        self.assertTrue(result["all_14_pairs_rehashed_from_actual_guest_bytes"])
        self.assertEqual(result["guest_entry_brackets"]["movie"][
            "exact_adjacent_onset_offset"], 316)
        self.assertEqual(result["guest_entry_brackets"]["original"][
            "exact_adjacent_onset_offset"], 315)
        self.assertEqual(result["guest_entry_brackets"]["native"][
            "exact_adjacent_onset_offset"], 318)
        self.assertEqual(result["independent_usa_event_adjudication"], "HOLD")
        self.assertEqual(result["accepted_usa_events"], 0)

    def test_missing_or_tampered_real_images_fail(self):
        self.make()
        path = self.replay / "native/dragster-next-zoo-315.wram.bin"
        raw = bytearray(path.read_bytes())
        raw[0x313] ^= 1
        path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "raw memory|WRAM byte"):
            audit.audit(self.root)
        self.make()
        path = self.replay / "ref/dragster-next-zoo-316.sram.bin"
        path.write_bytes(b"short")
        with self.assertRaisesRegex(ValueError, "short or oversized"):
            audit.audit(self.root)

    def test_forged_source_clock_and_gameplay_promotion_fail(self):
        report = self.make()
        report["dragster_next_zoo_handoff"]["release_complete_usa_event_credit"] = 1
        self.write("dragster-report.json", report)
        with self.assertRaisesRegex(ValueError, "over-promotional"):
            audit.audit(self.root)
        report = self.make()
        report["dragster_next_zoo_handoff"]["entry_brackets"]["native"][
            "exact_adjacent_onset_offset"] = 316
        self.write("dragster-report.json", report)
        with self.assertRaisesRegex(ValueError, "entry/bracket"):
            audit.audit(self.root)
        self.make()
        path = self.replay / "reference.log"
        path.write_text(path.read_text().replace(
            "script f=3342 dump dragster-next-zoo-316",
            "script f=3330 dump dragster-next-zoo-316"))
        with self.assertRaisesRegex(ValueError, "host clock"):
            audit.audit(self.root)

    def test_no_fake_earned_dragster_or_reported_zoo_payload_aggregate(self):
        report = self.make()
        report["dragster_next_zoo_handoff"][
            "original_native_ranked_checksum_valid_all_samples"] = False
        self.write("dragster-report.json", report)
        with self.assertRaisesRegex(ValueError, "score or course-payload"):
            audit.audit(self.root)
        report = self.make()
        report["dragster_next_zoo_handoff"][
            "fresh_native_loaded_true_zoo_course_while_active"] = False
        self.write("dragster-report.json", report)
        with self.assertRaisesRegex(ValueError, "score or course-payload"):
            audit.audit(self.root)

    def test_wrong_frozen_original_rom_movie_or_controller_rejected(self):
        for key in ("rom_sha256", "original_movie_sha256",
                    "source_sram_sha256", "input_sha256"):
            report = self.make()
            report[key] = "b" * 64
            self.write("dragster-report.json", report)
            with self.assertRaisesRegex(ValueError, "source-pinned"):
                audit.audit(self.root)

    def test_source_selection_is_not_active_zoo(self):
        self.make()
        actual = audit.movie_states_from_actual_trace(
            self.root / "dragster/source/trace.jsonl")
        self.assertEqual(actual[2935]["track"], 1)
        self.assertEqual(actual[2935]["in_race"], 0)
        self.assertEqual(actual[3189]["in_race"], 0)
        self.assertTrue(all(audit.active_zoo(actual[f]) for f in range(3190, 3198)))
        self.assertEqual(len(actual), 3210 - 2874 + 1)
        result = audit.audit(self.root)
        self.assertTrue(result["source_2014_8_consecutive_zoo_active_frames_rederived"])

    def test_source_early_active_false_positive_rejected(self):
        report = self.make()
        path = self.root / "dragster/source/trace.jsonl"
        text = path.read_text(encoding="utf8").replace(
            '"f":3190', '"f":3189')
        path.write_text(text, encoding="utf8")
        proof = report["original_source_event"]["source_next_zoo"]
        proof["original_source_trace_sha256"] = digest(path.read_bytes())
        self.write("dragster/source/dragster-next-zoo-original.json", proof)
        self.write("dragster-report.json", report)
        # The immutable real-source trace guard correctly rejects the tamper
        # first. Then override only that constant in this synthetic fixture
        # to exercise the separate no-early-Zoo source-state gate.
        with self.assertRaisesRegex(ValueError, "source raw trace digest"):
            audit.audit(self.root)
        with mock.patch.object(audit, "FROZEN_MOVIE_TRACE", proof["original_source_trace_sha256"]):
            with self.assertRaisesRegex(ValueError, "eight consecutive Zoo frames"):
                audit.audit(self.root)

    def test_source_trace_and_ranked_record_authentication(self):
        self.make()
        path = self.root / "dragster/source/trace.jsonl"
        path.write_text("forged source", encoding="utf8")
        with self.assertRaisesRegex(ValueError, "trace digest"):
            audit.audit(self.root)
        self.make()
        path = self.replay / "native/dragster-next-zoo-304.sram.bin"
        raw = bytearray(path.read_bytes())
        raw[0x422] ^= 1
        path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "ranked record|raw memory"):
            audit.audit(self.root)


if __name__ == "__main__":
    unittest.main()
