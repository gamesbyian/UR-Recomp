"""Adversarial ROM-free A/B artifact reviews; no emulators or retail ROM."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_frame_fingerprint as frames
import qa01_verify_frame_capture as independent
import qa01_independent_zoo_capture_ab_archive as audit


class SourceAuthenticAB(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        original, native = self.root / "original", self.root / "native"
        original.mkdir()
        native.mkdir()
        identity = {
            "source_sha": "a" * 40, "rom_sha256": "b" * 64,
            "movie_sha256": "c" * 64, "input_sha256": "d" * 64,
            "observation_phase": "post-script-dump",
            "original_frame_origin": 1017, "native_frame_origin": 1019,
            "masked_wram_bytes": 0, "masked_sram_bytes": 0,
        }
        for frame in range(3):
            for guest, folder, origin in (
                ("original", original, 1017),
                ("native", native, 1019),
            ):
                wram, sram = bytearray(frames.WRAM), bytearray(frames.SRAM)
                if guest == "native" and frame == 2:
                    wram[0x0063] = 1
                frames.snapshot_path(folder, frame + origin, "wram").write_bytes(wram)
                frames.snapshot_path(folder, frame + origin, "sram").write_bytes(sram)
        retained = self.root / "retained"
        fp = frames.audit(identity, original, native, 0, 2, retained=retained)
        checked = independent.verify(fp, retained)
        metrics = {
            "schema": "ur-qa01-source-acknowledged-frame-replay/1",
            "window": {"start": 0, "end": 2, "count": 3},
            "original_guest_acknowledged_frames": 3,
            "native_guest_acknowledged_frames": 3,
            "retained_full_raw_image_bytes": 2 * 2 * (131072 + 8192),
            "accepted_USA_events": 0,
            "same_guest_inputs_actually_consumed_proven": False,
        }
        off = {
            "name": "zoom-zoo", "rom_sha256": identity["rom_sha256"],
            "original_movie_sha256": identity["movie_sha256"],
            "comparison": {
                "paired_event_candidate": False,
                "terminal_result_frame_matched": False,
                "terminal_result_guest_frame": {
                    "reference_relative": 3, "native_relative": 2}},
            "zoo_race_mesh": {
                "masked_or_excluded_wram_bytes": 0,
                "every_gameplay_frame_compared": False},
            "zoo_next_bowl_handoff": {
                "release_complete_event_credit": 0,
                "fresh_reference_next_bowl_entry_offset": 267,
                "fresh_native_next_bowl_entry_offset": 266,
                "all_original_native_full_sram_pairs_equal": False,
                "next_bowl_entry_triple_equal": False},
            "reference_script_sha256": "e" * 64,
            "input_sha256": "e" * 64,
            "qa01_continuous_memory_capture": None,
            "qa01_capture_ab_control": {
                "schema": "ur-qa01-capture-ab-replay-control/1",
                "repository_source_sha": identity["source_sha"],
                "controller_movie_window_sha256": identity["input_sha256"],
                "reference_supplied_input_sha256": "1" * 64,
                "native_supplied_input_sha256": "2" * 64,
                "reference_supplied_input_bytes": 100,
                "native_supplied_input_bytes": 120,
                "reference_script_sha256": "e" * 64,
                "capturing_continuous_frames": False,
            },
        }
        on = copy.deepcopy(off)
        on["reference_script_sha256"] = "f" * 64
        on["input_sha256"] = "f" * 64
        on["qa01_capture_ab_control"]["reference_script_sha256"] = "f" * 64
        on["qa01_capture_ab_control"]["capturing_continuous_frames"] = True
        d_fp = json.dumps(fp, sort_keys=True).encode()
        d_check = json.dumps(checked, sort_keys=True).encode()
        on["qa01_continuous_memory_capture"] = {
            "fingerprints_sha256": hashlib.sha256(d_fp).hexdigest(),
            "independent_review_sha256": hashlib.sha256(d_check).hexdigest(),
            "metrics": metrics,
            "accepted_complete_USA_events": 0,
            "actual_cpu_joypad_poll_consumption_proven": False,
        }
        prefix = audit.RAW + "retained/"
        self.members = {
            audit.DOC["on"]: json.dumps(on).encode(),
            audit.DOC["off"]: json.dumps(off).encode(),
            audit.DOC["frames"]: d_fp,
            audit.DOC["review"]: d_check,
            audit.DOC["metrics"]: json.dumps(metrics).encode(),
            audit.DOC["ab"]: json.dumps({
                "admitted_usa_events": 0,
                "actual_input_CPU_read_trace_proven": False,
                "full_race_or_Windows_persistence_proven": False,
                "existing_semantic_observations_unchanged": True,
                "same_supplied_original_native_input_bytes_digest": True,
                "same_source_controller_and_binaries": True,
                "actual_complete_consecutive_frame_acknowledgments": 3,
                "bounded_capture_start": 0, "bounded_capture_end": 2,
                "retained_evidence_bytes": 2 * 2 * (131072 + 8192),
            }).encode(),
            audit.ROOT + "off/exit-code.txt": b"1\n",
            audit.ROOT + "on/exit-code.txt": b"1\n",
        }
        self.members.update({
            prefix + entry["member"]: (retained / entry["member"]).read_bytes()
            for entry in fp["raw_retained_members"]
        })

    def run_case(self, change=None):
        members = dict(self.members)
        if change is not None:
            change(members)
        archive = self.root / "artifact.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            for name, blob in members.items():
                z.writestr(name, blob)
        return audit.verify(
            archive, expected_sha=hashlib.sha256(archive.read_bytes()).hexdigest())

    @staticmethod
    def mutate_json(members, which, function):
        obj = json.loads(members[audit.DOC[which]])
        function(obj)
        members[audit.DOC[which]] = json.dumps(obj).encode()

    def test_reopens_real_raw_bytes_and_distinguishes_workflow_green_from_gameplay(self):
        receipt = self.run_case()
        self.assertEqual(receipt["capture_off_producer_exit"], 1)
        self.assertEqual(receipt["capture_on_producer_exit"], 1)
        self.assertEqual(receipt["actual_unmasked_byte_differences"], {"wram": 1, "sram": 0})
        self.assertEqual(receipt["retained_raw_files_independently_reopened"], 8)
        self.assertEqual(receipt["digest_only_frames_not_reopened"], 1)
        self.assertEqual(receipt["original_result_frame"], 3)
        self.assertEqual(receipt["native_result_frame"], 2)
        self.assertEqual(receipt["original_next_bowl"], 267)
        self.assertEqual(receipt["native_next_bowl"], 266)
        self.assertFalse(receipt["guest_acknowledgment_log_bytes_reopened"])
        self.assertFalse(receipt["guest_cpu_controller_polls_proven"])
        self.assertEqual(receipt["accepted_USA_events"], 0)
        self.assertEqual(receipt["adjudication"], "HOLD")

    def test_change_semantic_result_rejected_even_with_green_ab_header(self):
        def mutate(members):
            self.mutate_json(members, "on", lambda doc: doc["comparison"][
                "terminal_result_guest_frame"].update(native_relative=3))
        with self.assertRaisesRegex(ValueError, "changed original/native game"):
            self.run_case(mutate)

    def test_input_field_is_replay_script_not_controller_window(self):
        receipt = self.run_case()
        self.assertTrue(receipt["reported_game_state_unchanged_by_dump_insertion"])
        # Unlike the unchanged actual controller-window and supplied guest
        # input file hashes, this producer's top-level input_sha256 is the
        # augmented replay *command script*. All three script hashes must
        # agree WITHIN each producer, but differ from capture off to on.
        def corrupt(members):
            self.mutate_json(members, "on", lambda d: d.update(
                input_sha256="f" * 63 + "e"))
        with self.assertRaisesRegex(ValueError, "altered guest input"):
            self.run_case(corrupt)

    def test_false_exit_stable_claim_rejected(self):
        with self.assertRaisesRegex(ValueError, "both red producer exits"):
            self.run_case(lambda m: m.update({audit.ROOT + "on/exit-code.txt": b"0\n"}))

    def test_both_green_producer_processes_cannot_mask_known_strict_negative(self):
        def mutate(members):
            members[audit.ROOT + "off/exit-code.txt"] = b"0\n"
            members[audit.ROOT + "on/exit-code.txt"] = b"0\n"
        with self.assertRaisesRegex(ValueError, "both red producer exits"):
            self.run_case(mutate)

    def test_source_cannot_self_attest_cpu_reads_or_event_acceptance(self):
        for flag in ("actual_input_CPU_read_trace_proven",
                     "full_race_or_Windows_persistence_proven"):
            def mutate(members):
                self.mutate_json(members, "ab",
                                 lambda d: d.update({flag: True}))
            with self.subTest(flag=flag), self.assertRaisesRegex(
                    ValueError, "zero-credit bounded capture"):
                self.run_case(mutate)

    def test_tampered_actual_raw_memory_rejected(self):
        def mutate(members):
            name = next(n for n in members if n.endswith("native-relative-000002-wram.bin"))
            image = bytearray(members[name])
            image[0x63] ^= 0x80
            members[name] = bytes(image)
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.run_case(mutate)

    def test_missing_raw_or_forged_digest_only_unsupported(self):
        def remove(members):
            target = next(n for n in members if n.endswith("original-relative-000000-sram.bin"))
            del members[target]
        with self.assertRaisesRegex(ValueError, "raw original/native memory members"):
            self.run_case(remove)

    def test_wrong_source_and_modified_provenance_rejected(self):
        def mutate(members):
            self.mutate_json(members, "on", lambda d: d[
                "qa01_capture_ab_control"].update(controller_movie_window_sha256="a" * 64))
        with self.assertRaisesRegex(ValueError, "altered guest input"):
            self.run_case(mutate)

    def test_pinned_sha_required_even_for_valid_synthetic(self):
        # Test helper passes the synthetic SHA explicitly. Default accepts
        # only the one real archived ZIP and cannot confuse a mock with it.
        archive = self.root / "not-a-real-case.zip"
        archive.write_bytes(b"not a ZIP")
        with self.assertRaisesRegex(ValueError, "ZIP SHA256"):
            audit.verify(archive)


if __name__ == "__main__":
    unittest.main()
