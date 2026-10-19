"""Fail-closed source/guest research factory pilot preflight, ROM-free tests."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_factory_preflight as preflight
import qa01_verify_frame_capture as raw_verifier


def control():
    """Structurally coherent synthetic receipts, NOT real executed evidence."""
    checks = {k: True for k in preflight.REQUIRED_ATTESTATIONS}
    att = {"schema": preflight.SCHEMA, "source_sha": "a" * 40,
           "rom_sha256": "b" * 64, "movie_sha256": "c" * 64,
           "input_sha256": "d" * 64, "checks": checks}
    causal = {
        "schema": "ur-qa01-causal-window-readonly-report/1",
        "source_sha": att["source_sha"],
        "input_identity": {k: att[k] for k in
                           ("source_sha", "rom_sha256", "movie_sha256", "input_sha256")},
        "original_event_sha256": "e" * 64, "native_event_sha256": "f" * 64,
        "observation_phase": "post-script-dump",
        "original_window": {"checkpoint": 2},
        "native_window": {"checkpoint": 2},
        "accepted_complete_USA_events": 0,
        "complete_gameplay_or_instruction_equivalence_proven": False,
        "addresses": [{"causal_equivalence_proven": False,
                       "checkpoint_differs": True}],
    }
    identity = {**{k: att[k] for k in
                   ("source_sha", "rom_sha256", "movie_sha256", "input_sha256")},
                "observation_phase": "post-script-dump",
                "original_frame_origin": 1017, "native_frame_origin": 2017,
                "masked_wram_bytes": 0, "masked_sram_bytes": 0}
    coverage = {"start": 0, "end": 7, "continuous_at_declared_frame_phase": True,
                "between_frame_opcode_semantics_proven": False,
                "required_frames": 8, "observed_original_frames": 8,
                "observed_native_frames": 8}
    frames = {
        "schema": "ur-qa01-frame-fingerprint/1",
        "source_identity": identity,
        "coverage": coverage,
        "raw_retained_members": [],
        "full_unmasked_differing_byte_occurrences": {"wram": 1, "sram": 0},
        "accepted_USA_events": 0,
    }
    verified = {
        "schema": "ur-qa01-independent-frame-capture-audit/1",
        "source_sha": att["source_sha"], "complete_USA_events_accepted": 0,
        "source_memory_bytes_independently_recomputed_for_retained_frames": True,
        "fingerprint_report_canonical_sha256": raw_verifier.canonical_sha256(frames),
        "frame_source_identity": copy.deepcopy(identity),
        "verified_relative_frame_window": {
            "start": 0, "end": 7, "required_frames": 8,
            "observation_phase": identity["observation_phase"],
            "original_frame_origin": 1017, "native_frame_origin": 2017},
        "retained_raw_manifest_canonical_sha256":
            raw_verifier.canonical_sha256([]),
        "verified_differing_byte_occurrences": {"wram": 1, "sram": 0},
    }
    return att, causal, frames, verified

class FactoryPreflight(unittest.TestCase):
    def call(self, *args):
        return preflight.evaluate(*args, {"attestation": "a" * 64})

    def test_all_requirements_allow_only_ten_case_manual_pilot(self):
        result = self.call(*control())
        self.assertEqual(result["readiness"], "bounded_pilot_ready")
        self.assertEqual(result["allowed_next_case_count"], 10)
        self.assertFalse(result["automatic_dispatch_authorized"])
        self.assertFalse(result["one_thousand_or_more_cases_authorized"])
        self.assertEqual(result["independent_USA_events_accepted"], 0)

    def test_missing_reports_hold(self):
        att, causal, frames, verified = control()
        for args in ((att, None, frames, verified),
                     (att, causal, None, verified),
                     (att, causal, frames, None)):
            with self.subTest(args=args):
                result = self.call(*args)
                self.assertEqual(result["readiness"], "hold")
                self.assertEqual(result["allowed_next_case_count"], 0)

    def test_every_false_producer_attestation_blocks(self):
        for key in preflight.REQUIRED_ATTESTATIONS:
            att, causal, frames, verified = control()
            att["checks"][key] = False
            with self.subTest(key=key):
                result = self.call(att, causal, frames, verified)
                self.assertEqual(result["readiness"], "hold")
                self.assertIn(key, result["missing_or_negative_conditions"])

    def test_identity_masking_missing_frame_and_false_credit_rejected(self):
        for mutate in range(5):
            att, causal, frames, verified = control()
            if mutate == 0:
                frames["source_identity"]["input_sha256"] = "9" * 64
            elif mutate == 1:
                frames["source_identity"]["masked_wram_bytes"] = 1
            elif mutate == 2:
                frames["coverage"]["observed_native_frames"] = 7
            elif mutate == 3:
                causal["accepted_complete_USA_events"] = 1
            else:
                verified["complete_USA_events_accepted"] = 1
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                self.call(att, causal, frames, verified)

    def test_no_genuine_difference_holds_instead_of_spawning_factory(self):
        att, causal, frames, verified = control()
        causal["addresses"][0]["checkpoint_differs"] = False
        result = self.call(att, causal, frames, verified)
        self.assertIn("no_observed_mismatch_for_a_causal_discriminator",
                      result["missing_or_negative_conditions"])
        self.assertEqual(result["allowed_next_case_count"], 0)


if __name__ == "__main__":
    unittest.main()
