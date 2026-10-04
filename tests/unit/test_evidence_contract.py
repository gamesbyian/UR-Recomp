import unittest

from tools.evidence_contract import assertion, make_envelope, validate_envelope


class EvidenceContractTest(unittest.TestCase):
    def test_accepts_structured_success(self):
        envelope = make_envelope(
            evidence_type="unit-demo",
            producer="test",
            subject={"candidate": "x"},
            inputs={"fixture": "f"},
            assertions=[assertion("same-state", True)],
        )
        self.assertEqual(envelope["outcome"], "accepted")
        self.assertEqual(validate_envelope(envelope), [])

    def test_rejects_accepted_failed_assertion(self):
        envelope = {
            "schema_version": 1,
            "evidence_type": "unit-demo",
            "producer": "test",
            "subject": {},
            "inputs": {},
            "assertions": [{"name": "x", "passed": False}],
            "outcome": "accepted",
            "provenance": {"generated_at_utc": "2026-10-04T00:00:00Z"},
        }
        self.assertIn(
            "accepted evidence cannot contain a failed assertion",
            validate_envelope(envelope),
        )

    def test_duplicate_assertion_names_fail(self):
        envelope = make_envelope(
            evidence_type="unit-demo",
            producer="test",
            subject={},
            inputs={},
            assertions=[assertion("a", True), assertion("b", True)],
        )
        envelope["assertions"][1]["name"] = "a"
        self.assertIn("duplicate assertion name: a", validate_envelope(envelope))


if __name__ == "__main__":
    unittest.main()
