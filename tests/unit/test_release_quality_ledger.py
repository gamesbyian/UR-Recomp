import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "release_ledger_validator", ROOT / "tools/validate_release_quality_ledger.py"
)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(validator)


def baseline():
    return json.loads(
        (ROOT / "docs/RELEASE-QUALITY-LEDGER.json").read_text(encoding="utf-8")
    )


class ReleaseQualityLedgerTests(unittest.TestCase):
    def test_current_unverified_register_is_structurally_valid(self):
        data = baseline()
        self.assertEqual(len(data["gates"]), 12)
        self.assertEqual(validator.check_registry(data, ROOT), [])

    def test_pass_requires_exact_candidate_and_real_witness(self):
        data = baseline()
        gate = data["gates"][0]
        gate["status"] = "passed"
        self.assertTrue(any("passed without exact pinned" in x
                            for x in validator.check_registry(data, ROOT)))
        data["candidate"]["commit_sha"] = "a" * 40
        data["candidate"]["zip_sha256"] = "b" * 64
        gate["candidate_commit"] = "a" * 40
        self.assertTrue(any("passed without independent" in x
                            for x in validator.check_registry(data, ROOT)))
        gate["witnesses"] = [{
            "source_commit": "a" * 40,
            "artifact_sha256": "b" * 64,
            "source": "physical test report",
            "tested_at": "2026-10-08T12:30:00Z",
            "layer": "L2",
        }]
        self.assertTrue(any("below required layer" in x
                            for x in validator.check_registry(data, ROOT)))
        gate["witnesses"][0]["layer"] = "L4"
        self.assertEqual(validator.check_registry(data, ROOT), [])

    def test_current_source_contracts_and_journey_denominators_are_real(self):
        data = baseline()
        gate = data["gates"][0]
        gate["journeys"].append("J-99")
        self.assertTrue(any("unknown journey" in x
                            for x in validator.check_registry(data, ROOT)))
        gate["journeys"].pop()
        gate["evidence_refs"][0] = "docs/../bad.md"
        self.assertTrue(any("unsafe source contract" in x
                            for x in validator.check_registry(data, ROOT)))

    def test_cannot_declare_beta_with_unverified_gates(self):
        data = baseline()
        data["candidate"]["release_decision"] = "beta"
        errors = validator.check_registry(data, ROOT)
        self.assertTrue(any("unresolved gates" in x for x in errors))
        self.assertTrue(any("physical Windows" in x for x in errors))

    def test_duplicate_or_missing_gate_is_rejected(self):
        data = baseline()
        data["gates"][1]["id"] = "QA-01"
        errors = validator.check_registry(data, ROOT)
        self.assertTrue(any("duplicate" in x for x in errors))
        self.assertTrue(any("missing mandatory gates" in x for x in errors))

    def test_decision_and_hardware_fields_fail_closed(self):
        data = baseline()
        data["candidate"]["release_decision"] = "approved_beta"
        self.assertTrue(any("unknown release_decision" in x
                            for x in validator.check_registry(data, ROOT)))
        data["candidate"]["release_decision"] = []
        self.assertTrue(any("unknown release_decision" in x
                            for x in validator.check_registry(data, ROOT)))
        data["candidate"]["release_decision"] = "not_assessed"
        data["candidate"]["physical_hardware_verified"] = "false"
        self.assertTrue(any("must be boolean" in x
                            for x in validator.check_registry(data, ROOT)))

    def test_beta_cannot_be_declared_with_every_gate_waived_and_no_zip(self):
        data = baseline()
        data["candidate"]["release_decision"] = "beta"
        data["candidate"]["physical_hardware_verified"] = True
        for gate in data["gates"]:
            gate["status"] = "waived"
            gate["waiver_reason"] = "Limited scope"
            gate["waiver_approved_by"] = "QA reviewer"
            gate["waiver_approved_at"] = "2026-10-10T20:00:00Z"
        problems = validator.check_registry(data, ROOT)
        self.assertTrue(any("release decision requires an exact" in x for x in problems))
        self.assertTrue(any("physical hardware claim requires" in x for x in problems))

    def test_failed_gate_needs_actual_candidate_reproduction(self):
        data = baseline()
        data["gates"][0]["status"] = "failed"
        problems = validator.check_registry(data, ROOT)
        self.assertTrue(any("failed without exact pinned candidate" in x for x in problems))
        self.assertTrue(any("failed without independent recorded witnesses" in x for x in problems))

    def test_l5_promotion_needs_physical_confirmation_on_exact_candidate(self):
        data = baseline()
        data["candidate"]["commit_sha"] = "a" * 40
        data["candidate"]["zip_sha256"] = "b" * 64
        gate = data["gates"][3]  # QA-04 / L5
        gate["status"] = "passed"
        gate["candidate_commit"] = "a" * 40
        gate["witnesses"] = [{
            "source_commit": "a" * 40, "artifact_sha256": "b" * 64,
            "source": "docs/WINDOWS-CLEAN-MACHINE-ACCEPTANCE.md",
            "tested_at": "2026-10-10T20:00:00Z", "layer": "L5",
        }]
        self.assertTrue(any("L5 pass without physical" in x
                            for x in validator.check_registry(data, ROOT)))
        data["candidate"]["physical_hardware_verified"] = True
        self.assertEqual(validator.check_registry(data, ROOT), [])

    def test_evidence_requires_unambiguous_timestamp_and_reviewed_waiver(self):
        data = baseline()
        data["candidate"]["commit_sha"] = "a" * 40
        data["candidate"]["zip_sha256"] = "b" * 64
        gate = data["gates"][0]
        gate["status"] = "passed"
        gate["candidate_commit"] = "a" * 40
        gate["witnesses"] = [{
            "source_commit": "a" * 40, "artifact_sha256": "b" * 64,
            "source": "reproducer", "tested_at": "2026-10-10", "layer": "L4",
        }]
        self.assertTrue(any("timezone-aware ISO-8601" in x
                            for x in validator.check_registry(data, ROOT)))
        gate["witnesses"][0]["tested_at"] = "2026-10-10T20:00:00+00:00"
        self.assertEqual(validator.check_registry(data, ROOT), [])

        gate["status"] = "waived"
        gate["witnesses"] = []
        gate["waiver_reason"] = " "
        problems = validator.check_registry(data, ROOT)
        self.assertTrue(any("explicit rationale" in x for x in problems))
        self.assertTrue(any("named reviewer" in x for x in problems))
        self.assertTrue(any("review instant" in x for x in problems))
        gate["waiver_reason"] = "Documented limited-scope exception"
        gate["waiver_approved_by"] = "QA reviewer"
        gate["waiver_approved_at"] = "2026-10-10T20:00:00Z"
        self.assertEqual(validator.check_registry(data, ROOT), [])

    def test_malformed_scalar_types_report_errors_instead_of_crashing(self):
        data = baseline()
        data["gates"][0]["priority"] = ["P0"]
        data["gates"][1]["status"] = ["passed"]
        data["gates"][2]["required_layer"] = ["L4"]
        data["candidate"]["release_decision"] = {"state": "beta"}
        self.assertGreaterEqual(len(validator.check_registry(data, ROOT)), 4)

if __name__ == "__main__":
    unittest.main()
