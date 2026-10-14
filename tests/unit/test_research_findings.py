"""Evidence-driven research findings register: classification rules."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import research_findings as m


def finding(**over):
    base = {
        "id": "RF-900", "title": "t", "class": "reproducible_anomaly",
        "status": "open", "evidence": "native_only", "owner_lane": "research",
        "reproducer": {"command": "python3 tools/x.py", "runs": [38446393623]},
        "source_artifacts": ["a"], "uncertainty": "u",
        "resolving_experiment": "e", "consequence": "c",
    }
    base.update(over)
    return base


def register(*findings):
    return {"schema": m.SCHEMA, "release_gate_credit": 0, "findings": list(findings)}


class Register(unittest.TestCase):
    def test_committed_register_is_valid(self):
        data = json.loads(m.REGISTER.read_text(encoding="utf-8"))
        findings = m.validate(data)
        self.assertTrue(all(f["class"] in m.CLASSES for f in findings))
        self.assertIn("| RF-", m.render(findings))

    def test_discrepancy_requires_original_evidence_and_alignment(self):
        with self.assertRaisesRegex(ValueError, "original AND native"):
            m.validate(register(finding(**{"class": "original_native_discrepancy"})))
        aligned = finding(**{"class": "original_native_discrepancy",
                             "evidence": "original_and_native"})
        with self.assertRaisesRegex(ValueError, "race-relative"):
            m.validate(register(aligned))
        aligned["reproducer"]["race_relative_lag"] = 2
        m.validate(register(aligned))

    def test_fingerprint_novelty_is_never_an_open_assignment(self):
        with self.assertRaisesRegex(ValueError, "never an open"):
            m.validate(register(finding(**{"class": "fingerprint_novelty"})))
        with self.assertRaisesRegex(ValueError, "never an open"):
            m.validate(register(finding(**{"class": "fingerprint_novelty",
                                           "status": "retired", "resolution": "r"})))

    def test_closed_findings_record_resolution_and_handoffs_name_a_lane(self):
        with self.assertRaisesRegex(ValueError, "resolution"):
            m.validate(register(finding(status="resolved")))
        with self.assertRaisesRegex(ValueError, "receiving"):
            m.validate(register(finding(status="handed_off")))

    def test_rejects_credit_unknown_values_and_duplicates(self):
        bad = register(finding())
        bad["release_gate_credit"] = 1
        with self.assertRaisesRegex(ValueError, "credit"):
            m.validate(bad)
        for key, value in (("class", "novel"), ("status", "done"),
                           ("owner_lane", "everyone"), ("evidence", "vibes")):
            with self.assertRaises(ValueError):
                m.validate(register(finding(**{key: value})))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            m.validate(register(finding(), finding()))
        with self.assertRaisesRegex(ValueError, "run id"):
            m.validate(register(finding(reproducer={"command": "c", "runs": ["latest"]})))

    def test_queue_orders_by_decision_value(self):
        a = finding(id="RF-901", **{"class": "reproducible_anomaly"})
        b = finding(id="RF-902", **{"class": "original_native_discrepancy",
                                    "evidence": "original_and_native",
                                    "reproducer": {"command": "c", "race_relative_lag": 2}})
        c = finding(id="RF-903", status="retired", resolution="r")
        q = m.queue(m.validate(register(a, copy.deepcopy(b), c)))
        self.assertEqual([f["id"] for f in q], ["RF-902", "RF-901"])


if __name__ == "__main__":
    unittest.main()
