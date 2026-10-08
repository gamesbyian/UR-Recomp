"""Game-event-relative X/tabletop phase parity, including invalid witnesses."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from check_stunt_tabletop_phase import (  # noqa: E402
    TransientEvidenceError, normalized, verify,
)

SOURCE = ROOT / "analysis/generated/usjo8-x-tabletop-transient.json"


class TabletopPhaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(SOURCE.read_text(encoding="utf-8"))

    def test_retained_native_and_snes9x_are_event_relative_identical(self):
        report = verify(self.evidence)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual([r["relative_frame"] for r in report["phase_transitions"]], [0, 2, 4, 6, 8])
        self.assertEqual([r["val"] for r in report["phase_transitions"]], [1, 2, 3, 4, 0])
        self.assertEqual(report["kind"], "retained-reference-recheck")

    def test_new_captures_must_include_matched_quiet_control(self):
        base = self.evidence["observation"]
        report = verify(self.evidence, native=base["native"], reference=base["reference"], control=[])
        self.assertEqual(report["kind"], "new-event-relative-comparison")
        with self.assertRaisesRegex(TransientEvidenceError, "matched control"):
            verify(self.evidence, native=base["native"], reference=base["reference"], control=[{"frame": 1}])
        with self.assertRaisesRegex(TransientEvidenceError, "both engines"):
            verify(self.evidence, native=base["native"])

    def test_missing_or_shifted_or_reordered_samples_rejected(self):
        base = self.evidence["observation"]["native"]
        with self.assertRaisesRegex(TransientEvidenceError, "five"):
            normalized(base[:-1], "native")
        bad = copy.deepcopy(base)
        bad[2]["frame"] += 1
        with self.assertRaisesRegex(TransientEvidenceError, "two guest frames"):
            normalized(bad, "native")
        bad = copy.deepcopy(base)
        bad[2]["old"] = 0
        with self.assertRaisesRegex(TransientEvidenceError, "wrong phase"):
            normalized(bad, "native")
        bad = copy.deepcopy(base)
        bad[0]["frame"] = True
        with self.assertRaisesRegex(TransientEvidenceError, "noninteger"):
            normalized(bad, "native")

    def test_corrupt_retained_metadata_fails_closed(self):
        x = copy.deepcopy(self.evidence)
        x["causal_address"] = "7E:042B"
        with self.assertRaisesRegex(TransientEvidenceError, "address"):
            verify(x)
        x = copy.deepcopy(self.evidence)
        x["observation"]["absent_in_matched_control"] = False
        with self.assertRaisesRegex(TransientEvidenceError, "control"):
            verify(x)
        x = copy.deepcopy(self.evidence)
        x["observation"]["transition_values"][-1] = 9
        with self.assertRaisesRegex(TransientEvidenceError, "summary"):
            verify(x)


if __name__ == "__main__":
    unittest.main()
