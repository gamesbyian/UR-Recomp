"""Adversarial contract tests for the standing hosted-experiment service."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import agent_experiment_request as experiment

SHA = "a" * 40
REF = "refs/heads/experiments/rf095-attempt-1"


def request():
    return {
        "schema": experiment.SCHEMA,
        "kind": "qa01_rf095_pcm",
        "question": "Does actual original versus native PCM diverge at Zoo result?",
        "expected": "A bounded, source-pinned stereo PCM witness or a precise failure.",
        "owner": "fidelity",
        "attempt": 1,
    }


def encode(value):
    return json.dumps(value).encode("utf-8")


class AgentExperimentRequestTests(unittest.TestCase):
    def test_real_pcm_request_is_bound_but_never_accepted(self):
        r = experiment.validate_request(encode(request()), SHA, REF)
        self.assertEqual(r["request"]["kind"], "qa01_rf095_pcm")
        self.assertEqual(r["source_sha"], SHA)
        self.assertEqual(r["qualification_status"], "unreviewed_experiment")
        self.assertEqual(r["usa_course_credit"], 0)
        self.assertEqual(r["release_gate_credit"], 0)

    def test_all_allowlisted_runners(self):
        for kind in sorted(experiment.KINDS):
            with self.subTest(kind=kind):
                value = request()
                value["kind"] = kind
                self.assertEqual(experiment.validate_request(encode(value), SHA, REF)
                                 ["request"]["kind"], kind)

    def test_unknown_runner_and_injected_commands_are_denied(self):
        for kind in ("shell", "qa01_rf095_pcm; echo pwned", "../run", ""):
            with self.subTest(kind=kind):
                value = request()
                value["kind"] = kind
                with self.assertRaises(ValueError):
                    experiment.validate_request(encode(value), SHA, REF)

    def test_duplicate_keys_denied(self):
        raw = encode(request()).replace(b'"attempt": 1',
                                         b'"attempt": 1, "attempt": 2')
        with self.assertRaisesRegex(ValueError, "duplicate"):
            experiment.validate_request(raw, SHA, REF)

    def test_broken_source_and_ref_denied(self):
        for sha, ref in ((SHA[:12], REF), (SHA, "refs/heads/main"),
                         (SHA, "refs/heads/experiments/../../main"),
                         (SHA, "refs/heads/experiments/x//y")):
            with self.subTest(sha=sha, ref=ref):
                with self.assertRaises(ValueError):
                    experiment.validate_request(encode(request()), sha, ref)

    def test_boolean_attempt_and_extra_fields_denied(self):
        for bad in (True, 0, -1, 10001, "1", 1.0):
            with self.subTest(attempt=bad):
                value = request()
                value["attempt"] = bad
                with self.assertRaises(ValueError):
                    experiment.validate_request(encode(value), SHA, REF)
        value = request()
        value["shell"] = "curl -d @token"
        with self.assertRaises(ValueError):
            experiment.validate_request(encode(value), SHA, REF)

    def test_reject_control_characters_and_nonfinite_numbers(self):
        value = request()
        value["question"] += "\nextra command"
        with self.assertRaises(ValueError):
            experiment.validate_request(encode(value), SHA, REF)
        with self.assertRaises(ValueError):
            experiment.validate_request(encode(request()).replace(b'"attempt": 1',
                                         b'"attempt": NaN'), SHA, REF)

    def test_size_bound(self):
        raw = encode(request()) + b" " * 4200
        with self.assertRaises(ValueError):
            experiment.validate_request(raw, SHA, REF)


if __name__ == "__main__":
    unittest.main()
