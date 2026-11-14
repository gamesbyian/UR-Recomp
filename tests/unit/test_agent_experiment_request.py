"""Adversarial contract tests for the standing hosted-experiment service."""
import hashlib
import json
import tempfile
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

    def test_script_profile_requires_exact_source_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out = root / "experiments"
            out.mkdir()
            self.assertIsNone(experiment.script_digest("qa01_zoo", root))
            with self.assertRaisesRegex(ValueError, "regular"):
                experiment.script_digest("script_linux", root)
            script = out / "run.sh"
            sample = b"#!/usr/bin/env bash\nset -euo pipefail\nprintf 'real experiment'\n"
            script.write_bytes(sample)
            self.assertEqual(experiment.script_digest("script_linux", root),
                             hashlib.sha256(sample).hexdigest())
            for invalid in (b"#!/bin/sh\ntrue\n",
                            b"#!/usr/bin/env bash\n" + b"a" * 262144,
                            sample + b"\x00"):
                with self.subTest(raw_size=len(invalid)):
                    script.write_bytes(invalid)
                    with self.assertRaisesRegex(ValueError, "small, nonbinary"):
                        experiment.script_digest("script_linux", root)
            script.unlink()
            real = root / "real.sh"
            real.write_bytes(sample)
            script.symlink_to(real)
            with self.assertRaisesRegex(ValueError, "regular"):
                experiment.script_digest("script_linux", root)

    def test_script_request_keeps_source_and_zero_credits(self):
        raw = request()
        raw["kind"] = "script_linux"
        r = experiment.validate_request(encode(raw), SHA, REF)
        self.assertEqual(r["source_sha"], SHA)
        self.assertEqual(r["usa_course_credit"], 0)
        self.assertEqual(r["release_gate_credit"], 0)
        self.assertEqual(r["qualification_status"], "unreviewed_experiment")


if __name__ == "__main__":
    unittest.main()
