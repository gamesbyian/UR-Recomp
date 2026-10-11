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

    def test_empty_or_malformed_accepted_envelopes_fail_closed(self):
        base = make_envelope(
            evidence_type="unit-demo", producer="test",
            subject={}, inputs={},
            assertions=[assertion("proof", True)],
        )
        base["assertions"] = []
        self.assertIn("accepted evidence must contain a passing assertion",
                      validate_envelope(base))
        with self.assertRaisesRegex(ValueError, "accepted evidence must contain"):
            make_envelope(evidence_type="unit-demo", producer="test",
                          subject={}, inputs={}, assertions=[], outcome="accepted")
        base["assertions"] = [{"name": "proof", "passed": True}]
        for malformed in ([], {}, 123, False, None):
            with self.subTest(outcome=malformed):
                base["outcome"] = malformed
                self.assertTrue(any("outcome must be one of" in x
                                    for x in validate_envelope(base)))
        base["outcome"] = "accepted"
        base["schema_version"] = True
        self.assertIn("schema_version must be 1", validate_envelope(base))

    def test_timestamp_is_an_actual_timezone_aware_instant(self):
        envelope = make_envelope(
            evidence_type="unit-demo", producer="test",
            subject={}, inputs={}, assertions=[assertion("proof", True)],
        )
        for instant in ("yesterday", "2026-10-11", "2026-10-11T16:30:00",
                        "2026-99-99T12:00:00Z", [], None):
            with self.subTest(instant=instant):
                envelope["provenance"]["generated_at_utc"] = instant
                self.assertTrue(any("timezone-aware instant" in x
                                    for x in validate_envelope(envelope)))
        envelope["provenance"]["generated_at_utc"] = "2026-10-11T16:30:00Z"
        self.assertEqual(validate_envelope(envelope), [])

    def test_metrics_must_match_documented_schema_when_present(self):
        envelope = make_envelope(
            evidence_type="unit-demo", producer="test",
            subject={}, inputs={}, assertions=[assertion("proof", True)],
        )
        envelope["metrics"] = "not-an-object"
        self.assertIn("metrics must be an object", validate_envelope(envelope))

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
