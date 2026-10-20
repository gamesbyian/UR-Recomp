#!/usr/bin/env python3
"""R5 network-island diagnostic policy: deterministic claims, no network."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "tools/p2p/observed_connectivity_v0.py"
spec = importlib.util.spec_from_file_location("p2p_r5_observed", MODULE)
assert spec and spec.loader
diag = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = diag
spec.loader.exec_module(diag)


def sample(**changes):
    value = {
        "source": "manual",
        "descriptor": "signed_verified",
        "friend_confirmed": True,
        "simulation": "match",
        "direct": "not_tried",
        "manual_reply_received": False,
        "volunteer_relay_opt_in": False,
        "relay": "unavailable",
    }
    value.update(changes)
    return value


class OfflineR5Observations(unittest.TestCase):
    def status(self, expected, **changes):
        evidence = sample(**changes)
        result = diag.assess_mapping(evidence)
        self.assertEqual(result["status"], expected)
        self.assertEqual(result["evidence_class"], "OBSERVED_STAGES_ONLY")
        return result

    def test_no_infrastructure_can_never_be_classified_connected(self):
        self.status("NO_CONTACT", source="none", descriptor="absent")
        self.status("CONTACT_UNAUTHENTICATED",
                    descriptor="urp0_untrusted")
        self.status("CONTACT_EXPIRED", descriptor="expired")
        self.status("FRIEND_NOT_CONFIRMED", friend_confirmed=False)
        self.status("SIMULATION_INCOMPATIBLE", simulation="mismatch")
        self.status("SIMULATION_NOT_CHECKED", simulation="unknown")
        self.status("DIRECT_PROBE_REQUIRED")
        # A one-way code does NOT magically defeat NAT.
        reply = self.status("REPLY_CODE_SUGGESTED", direct="failed")
        self.assertIn("not guaranteed", reply["next_action"])
        self.status("NO_USABLE_ROUTE", direct="failed",
                    manual_reply_received=True, relay="unavailable")
        self.status("NO_USABLE_ROUTE", direct="failed",
                    manual_reply_received=True, relay="refused",
                    volunteer_relay_opt_in=True)
        self.status("NO_USABLE_ROUTE", source="lan", direct="failed",
                    relay="unavailable")
        self.status("VOLUNTEER_RELAY_PROBE_REQUIRED", direct="failed",
                    manual_reply_received=True,
                    relay="not_tried", volunteer_relay_opt_in=True)

    def test_authenticated_routes_are_observations_not_predictions(self):
        self.status("DIRECT_SESSION_CONFIRMED", direct="authenticated")
        self.status("VOLUNTEER_RELAY_SESSION_CONFIRMED",
                    direct="failed", relay="authenticated",
                    volunteer_relay_opt_in=True)
        result = self.status("DIRECT_SESSION_CONFIRMED", source="overlay",
                             direct="authenticated")
        self.assertIn("separately verified", result["next_action"])
        self.status("DIRECT_PROBE_REQUIRED", source="cache")
        self.status("DIRECT_PROBE_REQUIRED", source="lan")

    def test_reject_inconsistent_or_untrusted_stage_claims(self):
        invalid = [
            {"source": "none"},
            {"source": "none", "descriptor": "signed_verified"},
            {"source": "manual", "descriptor": "absent"},
            {"source": "lan", "manual_reply_received": True},
            {"relay": "authenticated"},
            {"direct": "authenticated", "relay": "authenticated",
             "volunteer_relay_opt_in": True},
            {"descriptor": "urp0_untrusted", "direct": "authenticated"},
            {"simulation": "mismatch", "direct": "authenticated"},
            {"friend_confirmed": False, "direct": "authenticated"},
            {"relay": "authenticated", "volunteer_relay_opt_in": True,
             "simulation": "unknown"},
        ]
        for change in invalid:
            with self.subTest(change=change), self.assertRaises(ValueError):
                diag.assess_mapping(sample(**change))
        for key, value in [
            ("source", "github"), ("descriptor", "self_signed"),
            ("simulation", "sometimes"), ("direct", "probably"),
            ("relay", "free"), ("friend_confirmed", 1),
            ("manual_reply_received", "false"), ("volunteer_relay_opt_in", 0)
        ]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                diag.assess_mapping(sample(**{key: value}))
        for value in [dict(sample(), secret="token"), {k:v for k,v in sample().items()
                                                       if k != "simulation"}, []]:
            with self.assertRaises(ValueError):
                diag.assess_mapping(value)

    def test_offline_cli_and_bounded_json(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "observations.json"
            path.write_text(json.dumps(sample(direct="failed",
                manual_reply_received=True)), encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(MODULE), str(path)],
                text=True, capture_output=True, timeout=10)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)["status"], "NO_USABLE_ROUTE")
            path.write_text("x" * (diag.MAX_EVIDENCE_BYTES + 10), encoding="utf-8")
            oversized = subprocess.run(
                [sys.executable, str(MODULE), str(path)],
                text=True, capture_output=True, timeout=10)
            self.assertEqual(oversized.returncode, 2)
            self.assertIn("bounded limit", oversized.stderr)

    def test_duplicate_and_exponent_overflow_rejected_at_file_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'observation.json'
            for raw in ('{"source":"manual","source":"none"}',
                        '{"descriptor":1e999}', '{"descriptor":NaN}'):
                path.write_text(raw, encoding='utf-8')
                run = subprocess.run([sys.executable, str(MODULE), str(path)],
                                     text=True, capture_output=True, timeout=10)
                self.assertEqual(run.returncode, 2, run.stderr)


if __name__ == "__main__":
    unittest.main()
