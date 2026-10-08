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
            "tested_at": "2026-10-08",
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


if __name__ == "__main__":
    unittest.main()
