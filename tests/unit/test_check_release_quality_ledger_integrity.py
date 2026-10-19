#!/usr/bin/env python3
"""Source ledger structural guards, not synthetic course/physical acceptance."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_release_quality_ledger_integrity as qa


def snapshot():
    return json.loads(qa.DEFAULT.read_text(encoding="utf-8"))


def synthetic_baseline():
    """Future valid release progress must not break adversarial fixture tests."""
    data = snapshot()
    data["candidate"].update(
        commit_sha=None, zip_sha256=None,
        physical_hardware_verified=False, release_decision="not_assessed")
    for gate in data["gates"]:
        gate.update(status="unverified", candidate_commit=None,
                    witnesses=[], waiver_reason=None)
    data["gates"][0]["coverage"].update(
        complete_event_passes=0, partial=4, unverified=41,
        regional_comparison_complete=0, regional_comparison_unverified=90)
    data["gates"][6]["coverage"]["complete_expert_event_passes"] = 0
    return data


class ReleaseQualityAuthority(unittest.TestCase):
    def check(self, changed):
        return qa.audit(changed)

    def test_live_ledger_preserves_explicit_current_authority(self):
        data = snapshot()
        result = self.check(data)
        self.assertEqual(
            result["candidate_fully_pinned"],
            data["candidate"]["commit_sha"] is not None)
        self.assertEqual(
            result["original_USA_complete_event_passes"],
            data["gates"][0]["coverage"]["complete_event_passes"])
        self.assertEqual(result["original_USA_total"], 45)
        self.assertEqual(result["approved_gate_count"], sum(
            gate["status"] == "passed" for gate in data["gates"]))
        self.assertEqual(result["pending_or_failed_gate_count"], sum(
            gate["status"] not in ("passed", "waived")
            for gate in data["gates"]))
        self.assertFalse(result["physical_windows_executed_here"])

    def test_free_prose_may_describe_green_hosted_smoke_without_promoting_gate(self):
        data = synthetic_baseline()
        data["gates"][4]["next_action"] += (
            " TEST ONLY: all virtual pads passed on synthetic fixture. "
            "This narrative alone is never a release decision."
        )
        self.assertEqual(self.check(data)["approved_gate_count"], 0)

    def test_forged_candidate_pins_waiver_and_zero_witness_gate_rejected(self):
        src, pin = "a" * 40, "b" * 64
        base = synthetic_baseline()
        cases = []
        def modified(fn):
            data = copy.deepcopy(base)
            fn(data)
            cases.append(data)
        modified(lambda d: d["candidate"].update(commit_sha=src))
        modified(lambda d: d["candidate"].update(zip_sha256=pin))
        modified(lambda d: d["candidate"].update(commit_sha=True))
        modified(lambda d: d["candidate"].update(
            commit_sha=src, zip_sha256="not-a-digest"))
        modified(lambda d: d["candidate"].update(physical_hardware_verified=1))
        modified(lambda d: d["candidate"].update(release_decision="approved"))
        modified(lambda d: d["gates"][4].update(status="passed"))
        modified(lambda d: d["gates"][4].update(status="failed"))
        modified(lambda d: d["gates"][4].update(status="waived"))
        modified(lambda d: d["gates"][4].update(
            waiver_reason="source-only green proves everything"))
        modified(lambda d: d["gates"][0].update(status="passed"))
        modified(lambda d: d["gates"][8].update(status="passed"))
        modified(lambda d: d["gates"][6].update(required_layer="synthetic"))
        for index, case in enumerate(cases):
            with self.subTest(case=index), self.assertRaises(ValueError):
                self.check(case)

    def test_full_witness_cannot_assume_45_courseruns_from_fewer_events(self):
        data = synthetic_baseline()
        bad_counts = (
            (1, 4, 41), (1, 4, 40), (46, 0, 0),
            (45, 0, 1), (-1, 4, 42), (True, 4, 40),
        )
        for complete, partial, missing in bad_counts:
            changed = copy.deepcopy(data)
            changed["gates"][0]["coverage"].update(
                complete_event_passes=complete,
                partial=partial,
                unverified=missing,
            )
            with self.subTest(count=complete), self.assertRaises(ValueError):
                self.check(changed)
        data["gates"][0]["coverage"].update(
            complete_event_passes=1, partial=4, unverified=40,
        )
        with self.assertRaisesRegex(ValueError, "oracle witness"):
            self.check(data)

    def test_legitimate_pinned_future_pass_needs_source_witness(self):
        data = synthetic_baseline()
        src, zip_digest = "a" * 40, "b" * 64
        data["candidate"].update(commit_sha=src, zip_sha256=zip_digest)
        gate = data["gates"][4]
        gate.update(status="passed", candidate_commit=src,
                    witnesses=[{"kind": "actual-windows-native",
                                "sha256": "c" * 64}])
        report = self.check(data)
        self.assertEqual(report["approved_gate_count"], 1)
        self.assertFalse(report["release_decision_structurally_admissible"])
        changed = copy.deepcopy(data)
        changed["gates"][4]["candidate_commit"] = "d" * 40
        with self.assertRaises(ValueError):
            self.check(changed)

    def test_completed_45_usa_gate_requires_all_scored_events_and_exact_witness(self):
        data = synthetic_baseline()
        data["candidate"].update(commit_sha="a" * 40,
                                 zip_sha256="b" * 64)
        gate = data["gates"][0]
        gate.update(status="passed", candidate_commit="a" * 40,
                    witnesses=[{"kind": "original-native-event-comparator",
                                "sha256": "c" * 64}])
        with self.assertRaisesRegex(ValueError, "unfinished"):
            self.check(data)
        gate["coverage"].update(complete_event_passes=45,
                                partial=0, unverified=0)
        self.assertEqual(self.check(data)["original_USA_complete_event_passes"], 45)
        self.assertFalse(self.check(data)["release_decision_structurally_admissible"])

    def test_both_auditors_refuse_one_machine_qa04_pass(self):
        data = synthetic_baseline()
        src, zhash = "a" * 40, "b" * 64
        data["candidate"].update(commit_sha=src, zip_sha256=zhash,
                                 physical_hardware_verified=True)
        gate = data["gates"][3]
        gate.update(status="passed", candidate_commit=src)

        def physical(label, clean=False):
            return {
                "source_commit": src, "artifact_sha256": zhash,
                "tested_executable_sha256": "c" * 64,
                "package_unchanged_after_launch": True,
                "source": "synthetic QA-04 setup, not authentic evidence",
                "tested_at": "2026-10-19T00:00:00Z", "layer": "L5",
                "hardware": {
                    "setup_id": label, "environment": "physical",
                    "clean_environment": clean,
                    "windows_version": "Windows 11 " + label,
                    "gpu": "GPU " + label,
                    "display": "Display " + label,
                    "controller": "Controller " + label,
                    "audio": "Audio " + label,
                    "physical_controller_observed": True,
                    "audible_output_observed": True,
                    "visible_display_observed": True,
                },
            }

        gate["witnesses"] = [physical("only-one", clean=True)]
        with self.assertRaisesRegex(ValueError, "fewer than three"):
            self.check(data)
        gate["witnesses"] = [physical("pc-a", clean=True),
                             physical("pc-b"), physical("pc-c")]
        self.assertEqual(self.check(data)["approved_gate_count"], 1)
        # A green structural test never executes any of these synthetic PCs.
        gate["witnesses"][2]["tested_executable_sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "fewer than three"):
            self.check(data)

    def test_release_ready_needs_all_gates_hardware_and_exact_candidate(self):
        data = synthetic_baseline()
        data["candidate"].update(commit_sha="a" * 40,
                                 zip_sha256="b" * 64,
                                 physical_hardware_verified=True,
                                 release_decision="approved")
        with self.assertRaisesRegex(ValueError, "pending gates"):
            self.check(data)


if __name__ == "__main__":
    unittest.main()
