"""ROM-free end-to-end QA01 factory admission, with real raw byte operations.

All fixtures are SYNTHETIC. They test fail-closed report coupling only and
never assert original game execution or shipping Windows QA.
"""
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
import qa01_verify_frame_capture as raw_verifier
import qa01_factory_preflight as preflight


def identity():
    return {"source_sha": "a" * 40, "rom_sha256": "b" * 64,
            "movie_sha256": "c" * 64, "input_sha256": "d" * 64}


def guest(who, byte):
    return {
        **identity(), "schema": causal.SCHEMA, "guest": who,
        "window": {"start": 0, "checkpoint": 1, "end": 2,
                   "phase": "post-script-dump", "addresses": ["7E:01ED"],
                   "complete": True, "overflow": False},
        "observed": {"7E:01ED": byte},
        "events": [
            {"seq": 1, "frame": 0, "clock": 1, "clock_domain": "cpu-local",
             "kind": "write", "address": "7E:01ED", "value": byte, "pc": "82D4F0"},
            {"seq": 2, "frame": 1, "clock": 2, "clock_domain": "cpu-local",
             "kind": "checkpoint", "phase": "post-script-dump"},
            {"seq": 3, "frame": 2, "clock": 3, "clock_domain": "cpu-local",
             "kind": "read", "address": "7E:01ED", "value": byte, "pc": "82D4F2"},
        ],
    }


def jhash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class FactoryPreflight(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        original, native, evidence = (root / name for name in ("original", "native", "raw"))
        original.mkdir()
        native.mkdir()
        for frame in range(3):
            for directory, origin, byte in ((original, 1017, 0x26),
                                            (native, 2017, 0x81)):
                memory = bytearray(frames.WRAM)
                memory[0x1ED] = byte
                frames.snapshot_path(directory, origin + frame, "wram").write_bytes(memory)
                frames.snapshot_path(directory, origin + frame, "sram").write_bytes(
                    bytes(frames.SRAM))
        frame_identity = {**identity(), "observation_phase": "post-script-dump",
                          "original_frame_origin": 1017, "native_frame_origin": 2017,
                          "masked_wram_bytes": 0, "masked_sram_bytes": 0}
        f = frames.audit(frame_identity, original, native, 0, 2, retained=evidence)
        v = raw_verifier.verify(f, evidence)
        a, b = guest("original", 0x26), guest("native", 0x81)
        c = causal.assess(a, b, json.dumps(a).encode(), json.dumps(b).encode())
        att = {**identity(), "schema": preflight.SCHEMA,
               "checks": {key: True for key in preflight.REQUIRED_ATTESTATIONS}}
        hashes = {"attestation": "e" * 64,
                  "causal_report": jhash(c), "frame_report": jhash(f),
                  "independent_raw_report": jhash(v)}
        att["evidence_sha256"] = {key: hashes[key] for key in preflight.REPORTS}
        self.att, self.causal, self.frames, self.verified = att, c, f, v
        self.hashes, self.raw_root = hashes, evidence
        self.original_event_bytes, self.native_event_bytes = (json.dumps(a).encode(),
                                                             json.dumps(b).encode())
        self.hashes["original_event_payload"] = hashlib.sha256(self.original_event_bytes).hexdigest()
        self.hashes["native_event_payload"] = hashlib.sha256(self.native_event_bytes).hexdigest()

    def check(self, att=None, c=None, f=None, v=None, raw=True, hashes=None, events=True):
        return preflight.evaluate(att if att is not None else self.att,
                                  c if c is not None else self.causal,
                                  f if f is not None else self.frames,
                                  v if v is not None else self.verified,
                                  hashes if hashes is not None else self.hashes,
                                  raw_root=self.raw_root if raw else None,
                                  original_event_bytes=self.original_event_bytes if events else None,
                                  native_event_bytes=self.native_event_bytes if events else None)

    def test_real_bytes_read_back_for_qualified_bounded_diagnostic(self):
        r = self.check()
        self.assertEqual(r["readiness"], "bounded_pilot_ready")
        self.assertEqual(r["raw_checkpoint_crosscheck"]["relative_frame"], 1)
        self.assertEqual(r["raw_checkpoint_crosscheck"]["causal_differences_recomputed_from_raw"], 1)
        self.assertEqual(r["allowed_next_case_count"], 10)
        self.assertFalse(r["automatic_dispatch_authorized"])
        self.assertFalse(r["one_thousand_or_more_cases_authorized"])
        self.assertEqual(r["independent_USA_events_accepted"], 0)

    def test_missing_raw_is_hold_even_with_all_green_review_flags(self):
        r = self.check(raw=False)
        self.assertEqual(r["readiness"], "hold")
        self.assertIn("missing_retained_raw_dir_for_independent_reopen",
                      r["missing_or_negative_conditions"])

    def test_legacy_attestation_is_hold(self):
        att = copy.deepcopy(self.att)
        att["schema"] = preflight.LEGACY_SCHEMA
        r = self.check(att=att)
        self.assertIn("legacy_attestation_lacks_report_pins", r["missing_or_negative_conditions"])

    def test_all_false_original_native_provenance_flags_hold(self):
        for key in preflight.REQUIRED_ATTESTATIONS:
            att = copy.deepcopy(self.att)
            att["checks"][key] = False
            with self.subTest(key=key):
                r = self.check(att=att)
                self.assertEqual(r["allowed_next_case_count"], 0)
                self.assertIn(key, r["missing_or_negative_conditions"])

    def test_missing_source_reports_not_replaced_with_green(self):
        for missing in preflight.REPORTS:
            args = dict(att=self.att, c=self.causal, f=self.frames, v=self.verified)
            args[{"causal_report": "c", "frame_report": "f",
                  "independent_raw_report": "v"}[missing]] = None
            # Exercise the API directly because None is the default shortcut
            with self.subTest(missing=missing):
                r = preflight.evaluate(args["att"], args["c"], args["f"], args["v"],
                                       self.hashes, raw_root=self.raw_root,
                                       original_event_bytes=self.original_event_bytes,
                                       native_event_bytes=self.native_event_bytes)
                self.assertEqual(r["readiness"], "hold")

    def test_pinned_review_rejects_swapped_or_replaced_report(self):
        wrong = copy.deepcopy(self.hashes)
        wrong["causal_report"] = "7" * 64
        with self.assertRaisesRegex(ValueError, "digest pin disagrees"):
            self.check(hashes=wrong)

    def test_missing_executed_event_payloads_is_hold(self):
        r = self.check(events=False)
        self.assertEqual(r["readiness"], "hold")
        self.assertIn("missing_actual_original_native_event_payloads",
                      r["missing_or_negative_conditions"])

    def test_forged_guest_pc_in_original_event_payload_is_rejected(self):
        src = json.loads(self.original_event_bytes)
        src["events"][2]["pc"] = "82D4FF"
        raw = json.dumps(src).encode()
        digests = dict(self.hashes)
        digests["original_event_payload"] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, "does not reproduce from actual event"):
            preflight.evaluate(self.att, self.causal, self.frames, self.verified,
                               digests, raw_root=self.raw_root,
                               original_event_bytes=raw,
                               native_event_bytes=self.native_event_bytes)

    def test_event_payload_digest_not_a_temporary_claim(self):
        digests = dict(self.hashes)
        digests["native_event_payload"] = "9" * 64
        with self.assertRaisesRegex(ValueError, "event payload digest changed"):
            self.check(hashes=digests)

    def test_missing_report_file_digest_cannot_inherit_green_attestation(self):
        incomplete = copy.deepcopy(self.hashes)
        incomplete.pop("frame_report")
        r = self.check(hashes=incomplete)
        self.assertEqual(r["readiness"], "hold")
        self.assertIn("missing_actual_report_file_sha256",
                      r["missing_or_negative_conditions"])

    def test_missing_attested_report_pins_is_hold(self):
        att = copy.deepcopy(self.att)
        att.pop("evidence_sha256")
        r = self.check(att=att)
        self.assertEqual(r["readiness"], "hold")
        self.assertIn("missing_independent_report_digest_pins",
                      r["missing_or_negative_conditions"])

    def test_original_native_byte_mutation_rejected_even_when_flags_claim_green(self):
        c = copy.deepcopy(self.causal)
        c["addresses"][0]["original"]["checkpoint_byte"] = 0x25
        with self.assertRaisesRegex(ValueError, "not from the retained"):
            self.check(c=c, events=False)

    def test_observation_phase_mismatch_rejected(self):
        c = copy.deepcopy(self.causal)
        c["observation_phase"] = "pre-nmi"
        with self.assertRaisesRegex(ValueError, "observation phase differs"):
            self.check(c=c, events=False)

    def test_wrong_causal_frame_rejected(self):
        c = copy.deepcopy(self.causal)
        c["original_window"]["checkpoint"] = 3
        c["native_window"]["checkpoint"] = 3
        with self.assertRaisesRegex(ValueError, "not in the real frame"):
            self.check(c=c, events=False)

    def test_forged_independent_raw_audit_and_missing_raw_byte_rejected(self):
        v = copy.deepcopy(self.verified)
        v["verified_raw_files"] -= 4
        with self.assertRaisesRegex(ValueError, "does not describe provided"):
            self.check(v=v)
        path = self.raw_root / "native-relative-000001-wram.bin"
        data = bytearray(path.read_bytes())
        data[0x1ED] ^= 1
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.check()

    def test_unsupported_release_promotion_rejected(self):
        f = copy.deepcopy(self.frames)
        f["accepted_USA_events"] = 1
        with self.assertRaisesRegex(ValueError, "release credit"):
            self.check(f=f)

    def test_no_real_discrepancy_does_not_authorize_factory(self):
        c = copy.deepcopy(self.causal)
        c["addresses"][0]["checkpoint_differs"] = False
        with self.assertRaisesRegex(ValueError, "flag disagrees"):
            self.check(c=c, events=False)


if __name__ == "__main__":
    unittest.main()
