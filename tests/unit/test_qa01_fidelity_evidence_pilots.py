"""ROM-free negative-contract tests for bounded QA01 causal and frame pilots."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_causal_window as causal
import qa01_frame_fingerprint as frames
import qa01_verify_frame_capture as verify_frame


def identities():
    return {"source_sha": "1" * 40, "rom_sha256": "2" * 64,
            "movie_sha256": "3" * 64, "input_sha256": "4" * 64}


def causal_guest(guest, value):
    data = {
        "schema": causal.SCHEMA, "guest": guest, **identities(),
        "window": {"start": 0, "checkpoint": 1, "end": 3,
                   "phase": "post-script-dump",
                   "addresses": ["7E:01ED"], "complete": True, "overflow": False},
        "observed": {"7E:01ED": value},
        "events": [
            {"seq": 1, "frame": 0, "clock": 1, "clock_domain": "cpu-master",
             "kind": "write", "address": "7E:01ED", "value": value, "pc": "82D4F0"},
            {"seq": 2, "frame": 1, "clock": 2, "clock_domain": "cpu-master",
             "kind": "checkpoint", "phase": "post-script-dump"},
            {"seq": 3, "frame": 2, "clock": 3, "clock_domain": "cpu-master",
             "kind": "read", "address": "7E:01ED", "value": value, "pc": "82D4F2"},
            {"seq": 4, "frame": 3, "clock": 4, "clock_domain": "cpu-master",
             "kind": "write", "address": "7E:01ED", "value": 0, "pc": "82D4F5"},
        ],
    }
    return data


class CausalWindowTests(unittest.TestCase):
    def report(self, a=None, b=None):
        a = a or causal_guest("original", 0x26)
        b = b or causal_guest("native", 0x81)
        return causal.assess(a, b, json.dumps(a).encode(), json.dumps(b).encode())

    def test_two_observed_reads_same_pc_are_candidate_not_accepted(self):
        result = self.report()
        first = result["addresses"][0]
        self.assertTrue(first["candidate_consumed_value_difference"])
        self.assertTrue(first["matching_guest_pc_of_first_read"])
        self.assertFalse(first["causal_equivalence_proven"])
        self.assertEqual(first["native"]["first_actual_read_before_overwrite"]["value"], 0x81)
        self.assertEqual(result["accepted_complete_USA_events"], 0)

    def test_provenance_window_phase_and_overflow_fail_closed(self):
        for mutation in ("sha", "phase", "overflow", "seq", "value"):
            a, b = causal_guest("original", 0x26), causal_guest("native", 0x81)
            if mutation == "sha":
                b["input_sha256"] = "5" * 64
            elif mutation == "phase":
                b["window"]["phase"] = "pre-nmi"
                b["events"][1]["phase"] = "pre-nmi"
            elif mutation == "overflow":
                b["window"]["overflow"] = True
            elif mutation == "seq":
                b["events"][2]["seq"] = 2
            else:
                b["events"][2]["value"] = 0x82
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.report(a, b)

    def test_overwritten_first_does_not_prove_never_consumed(self):
        a, b = causal_guest("original", 0x26), causal_guest("native", 0x81)
        for data in (a, b):
            data["events"][2]["kind"] = "write"
        result = self.report(a, b)
        item = result["addresses"][0]
        self.assertEqual(item["original"]["fate"], "overwritten_before_read")
        self.assertIsNone(item["native"]["first_actual_read_before_overwrite"])
        self.assertFalse(item["native"]["proves_never_read_during_entire_race"])

    def test_precheckpoint_last_writer_must_match_raw_checkpoint(self):
        a, b = causal_guest("original", 0x26), causal_guest("native", 0x81)
        a["events"][0]["value"] = 0x25
        # The subsequent real checkpoint and first read still agree, so this
        # used to pass even though the alleged last bus writer did not.
        with self.assertRaisesRegex(ValueError, "last executed writer"):
            self.report(a, b)

    def test_read_must_track_last_executed_write_on_either_side_of_checkpoint(self):
        for before in (True, False):
            a, b = causal_guest("original", 0x26), causal_guest("native", 0x81)
            if before:
                bad_read = {"frame": 0, "clock": 1, "clock_domain": "cpu-master",
                            "kind": "read", "address": "7E:01ED", "value": 0x25,
                            "pc": "82D4F1"}
                a["events"].insert(1, bad_read)
            else:
                bad_read = {"frame": 3, "clock": 5, "clock_domain": "cpu-master",
                            "kind": "read", "address": "7E:01ED", "value": 0x26,
                            "pc": "82D4F6"}
                a["events"].append(bad_read)
            for index, event in enumerate(a["events"], 1):
                event["seq"] = index
            with self.subTest(before_checkpoint=before), self.assertRaisesRegex(
                    ValueError, "actual read conflicts"):
                self.report(a, b)

    def test_host_frame_regression_invalidates_bus_event_order(self):
        a, b = causal_guest("original", 0x26), causal_guest("native", 0x81)
        a["events"][2]["frame"] = 0
        with self.assertRaisesRegex(ValueError, "host frame regressed"):
            self.report(a, b)

    def test_unknown_prior_writer_does_not_fabricate_a_memory_contradiction(self):
        a, b = causal_guest("original", 0x26), causal_guest("native", 0x81)
        # A bounded window need not include the write that established its
        # first byte. The real checkpoint seeds the first known observation.
        a["events"].pop(0)
        for index, event in enumerate(a["events"], 1):
            event["seq"] = index
        report = self.report(a, b)
        self.assertIsNone(report["addresses"][0]["original"]["last_observed_writer_before_checkpoint"])
        self.assertFalse(report["addresses"][0]["causal_equivalence_proven"])
        self.assertEqual(report["accepted_complete_USA_events"], 0)

    def test_multiple_clock_domains_are_not_cross_compared(self):
        a, b = causal_guest("original", 0x26), causal_guest("native", 0x81)
        for data in (a, b):
            data["events"][2]["clock_domain"] = "spc-local"
            data["events"][2]["clock"] = 1
        self.assertEqual(self.report(a, b)["accepted_complete_USA_events"], 0)
        b["events"][3]["clock"] = 0
        with self.assertRaisesRegex(ValueError, "clock regressed"):
            self.report(a, b)


class FrameFingerprintTests(unittest.TestCase):
    def identity(self):
        return {**identities(), "observation_phase": "post-script-dump",
                "original_frame_origin": 1017, "native_frame_origin": 2017,
                "masked_wram_bytes": 0, "masked_sram_bytes": 0}

    def make_capture(self, root):
        original = root / "original"
        native = root / "native"
        original.mkdir()
        native.mkdir()
        for rel in range(3):
            for guest, directory, origin in (("original", original, 1017),
                                             ("native", native, 2017)):
                w = bytearray(frames.WRAM)
                s = bytearray(frames.SRAM)
                if guest == "native" and rel == 1:
                    w[0x1ED] = 1
                if guest == "native" and rel == 2:
                    s[42] = 2
                frames.snapshot_path(directory, origin + rel, "wram").write_bytes(w)
                frames.snapshot_path(directory, origin + rel, "sram").write_bytes(s)
        return original, native

    def test_three_complete_frames_differences_and_hashed_retained_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a, b = self.make_capture(root)
            r = frames.audit(self.identity(), a, b, 0, 2, retained=root / "evidence")
            self.assertEqual(r["coverage"]["required_frames"], 3)
            self.assertEqual(r["full_unmasked_differing_byte_occurrences"], {"wram": 1, "sram": 1})
            self.assertEqual(r["first_differing_relative_frame"], {"wram": 1, "sram": 2})
            self.assertEqual(len(r["raw_retained_members"]), 12)
            self.assertEqual(r["accepted_USA_events"], 0)

    def test_independent_reopen_and_corrupted_raw_pair_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a, b = self.make_capture(root)
            evidence = root / "evidence"
            report = frames.audit(self.identity(), a, b, 0, 2, retained=evidence)
            verdict = verify_frame.verify(report, evidence)
            self.assertEqual(verdict["verified_raw_files"], 12)
            self.assertEqual(verdict["verified_differing_byte_occurrences"], {"wram": 1, "sram": 1})
            self.assertEqual(verdict["complete_USA_events_accepted"], 0)
            member = evidence / "native-relative-000001-wram.bin"
            changed = bytearray(member.read_bytes())
            changed[0x1ED] ^= 0x40
            member.write_bytes(changed)
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                verify_frame.verify(report, evidence)

    def test_raw_verdict_binds_exact_frame_report_not_merely_source_sha(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a, b = self.make_capture(root)
            long_report = frames.audit(
                self.identity(), a, b, 0, 2, retained=root / "long-raw")
            short_report = frames.audit(
                self.identity(), a, b, 0, 1, retained=root / "short-raw")
            long = verify_frame.verify(long_report, root / "long-raw")
            short = verify_frame.verify(short_report, root / "short-raw")
            # Two genuine independently reopened verdicts for the very same
            # source, ROM, movie, input and observation phase cannot be
            # substituted for each other by a downstream factory preflight.
            self.assertEqual(long["source_sha"], short["source_sha"])
            self.assertEqual(long["frame_source_identity"],
                             short["frame_source_identity"])
            self.assertNotEqual(
                long["fingerprint_report_canonical_sha256"],
                short["fingerprint_report_canonical_sha256"])
            self.assertEqual(long["verified_relative_frame_window"],
                             {"start": 0, "end": 2, "required_frames": 3,
                              "observation_phase": "post-script-dump",
                              "original_frame_origin": 1017,
                              "native_frame_origin": 2017})
            self.assertEqual(short["verified_relative_frame_window"]["end"], 1)
            self.assertEqual(long["fingerprint_report_canonical_sha256"],
                             verify_frame.canonical_sha256(long_report))
            # JSON key order and insignificant whitespace are not evidence
            # changes; an actual source identity or phase mutation IS.
            roundtrip = json.loads(json.dumps(long_report, indent=4))
            self.assertEqual(long["fingerprint_report_canonical_sha256"],
                             verify_frame.canonical_sha256(roundtrip))
            phased = copy.deepcopy(long_report)
            phased["source_identity"]["observation_phase"] = "other-guest-phase"
            other = verify_frame.verify(phased, root / "long-raw")
            self.assertEqual(long["source_sha"], other["source_sha"])
            self.assertNotEqual(long["fingerprint_report_canonical_sha256"],
                                other["fingerprint_report_canonical_sha256"])
            self.assertNotEqual(long["frame_source_identity"],
                                other["frame_source_identity"])
            self.assertEqual(long["retained_raw_manifest_canonical_sha256"],
                             verify_frame.canonical_sha256(sorted(
                                 long_report["raw_retained_members"],
                                 key=lambda row: row["member"])))
            self.assertEqual(long["complete_USA_events_accepted"], 0)

    def test_independent_verifier_refuses_lost_or_forged_capture(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a, b = self.make_capture(root)
            evidence = root / "evidence"
            report = frames.audit(self.identity(), a, b, 0, 2, retained=evidence)
            forged = copy.deepcopy(report)
            forged["rows"][1]["types"]["wram"]["unmasked_differing_byte_count"] = 0
            with self.assertRaises(ValueError):
                verify_frame.verify(forged, evidence)
            forged = copy.deepcopy(report)
            forged["raw_retained_members"].pop()
            with self.assertRaisesRegex(ValueError, "missing"):
                verify_frame.verify(forged, evidence)
            forged = copy.deepcopy(report)
            forged["first_differing_relative_frame"]["wram"] = 2
            with self.assertRaisesRegex(ValueError, "first differing frame"):
                verify_frame.verify(forged, evidence)
            forged = copy.deepcopy(report)
            forged["accepted_USA_events"] = 1
            with self.assertRaisesRegex(ValueError, "unsupported course promotion"):
                verify_frame.verify(forged, evidence)
            forged = copy.deepcopy(report)
            forged["coverage"]["observed_native_frames"] = 2
            with self.assertRaisesRegex(ValueError, "incomplete"):
                verify_frame.verify(forged, evidence)

    def test_unretained_interior_digest_disagrees_with_zero_count(self):
        # The middle frame is digest-only, so the independent reader cannot
        # reopen it. A forged digest with a recomputed valid digest chain used
        # to pass despite contradicting the declared zero unequal bytes.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a, b = self.make_capture(root)
            frames.snapshot_path(b, 2018, "wram").write_bytes(bytes(frames.WRAM))
            frames.snapshot_path(b, 2019, "sram").write_bytes(bytes(frames.SRAM))
            evidence = root / "evidence"
            report = frames.audit(self.identity(), a, b, 0, 2, retained=evidence)
            self.assertEqual(len(report["raw_retained_members"]), 8)
            baseline = verify_frame.verify(report, evidence)
            self.assertEqual(baseline["digest_only_equal_frames_not_independently_reopened"], 1)
            forged = copy.deepcopy(report)
            forged["rows"][1]["types"]["wram"]["native_sha256"] = "e" * 64
            chain = hashlib.sha256()
            for row in forged["rows"]:
                for kind in ("wram", "sram"):
                    for guest in ("original", "native"):
                        chain.update(bytes.fromhex(row["types"][kind][guest + "_sha256"]))
            forged["frame_pair_digest_chain_sha256"] = chain.hexdigest()
            with self.assertRaisesRegex(ValueError, "digest/count inconsistency"):
                verify_frame.verify(forged, evidence)

    def test_cannot_self_assert_external_source_or_windows_attestations(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a, b = self.make_capture(root)
            evidence = root / "evidence"
            report = frames.audit(self.identity(), a, b, 0, 2, retained=evidence)
            for flag in ("producer_binary_and_executed_input_independently_verified",
                         "windows_disk_persistence_proven"):
                forged = copy.deepcopy(report)
                forged[flag] = True
                with self.subTest(flag=flag), self.assertRaisesRegex(
                        ValueError, "unsupported external"):
                    verify_frame.verify(forged, evidence)

    def test_unmanifested_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a, b = self.make_capture(root)
            evidence = root / "evidence"
            report = frames.audit(self.identity(), a, b, 0, 2, retained=evidence)
            (evidence / "unlisted").mkdir()
            with self.assertRaisesRegex(ValueError, "unmanifested"):
                verify_frame.verify(report, evidence)

    def test_missing_short_masked_and_same_root_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a, b = self.make_capture(root)
            frames.snapshot_path(a, 1018, "sram").unlink()
            with self.assertRaisesRegex(ValueError, "missing"):
                frames.audit(self.identity(), a, b, 0, 2)
            frames.snapshot_path(a, 1018, "sram").write_bytes(bytes(100))
            with self.assertRaisesRegex(ValueError, "truncated"):
                frames.audit(self.identity(), a, b, 0, 2)
            identity = self.identity()
            identity["masked_wram_bytes"] = 1
            with self.assertRaisesRegex(ValueError, "unmasked"):
                frames.audit(identity, a, b, 0, 2)
            with self.assertRaisesRegex(ValueError, "cannot be identical"):
                frames.audit(self.identity(), a, a, 0, 2)

    def test_no_silent_retention_truncation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a, b = self.make_capture(root)
            target = root / "evidence"
            with self.assertRaisesRegex(ValueError, "cap exceeded"):
                frames.audit(self.identity(), a, b, 0, 2, retained=target, max_retained=2)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
