"""The three-project reuse register must be actionable, grounded and non-authoritative."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.select_three_project_reuse import candidates, context_hint, read_json, validate

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "analysis/three-project-reuse-opportunities.json"
MATRIX = ROOT / "analysis/data/three-project-apparatus-capability-matrix-20261010.json"
LANES = ROOT / "analysis/agent-context-lanes.json"


class ThreeProjectReuseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.register = read_json(REGISTER)
        cls.matrix = read_json(MATRIX)
        cls.lanes = read_json(LANES)

    def test_real_pinned_matrix_references_and_lanes(self):
        self.assertEqual(validate(self.register, self.matrix, self.lanes), [])
        self.assertGreaterEqual(len(self.register["entries"]), 10)
        self.assertEqual(
            len({x["id"] for x in self.register["entries"]}),
            len(self.register["entries"]),
        )

    def test_now_first_and_blocked_hidden_by_default(self):
        found = candidates(self.register, self.matrix, lane="release-qa")
        self.assertTrue(found)
        self.assertTrue(all(x["activation"] == "now" for x in found))
        self.assertIn("first-divergence", {x["id"] for x in found})
        self.assertNotIn("effective-address-access", {x["id"] for x in found})
        self.assertFalse(any(x["id"] == "differential-fuzzing" for x in found))

    def test_adversarial_source_lanes_and_modes(self):
        choices = candidates(self.register, self.matrix, lane="release-qa",
                             focus="NMI", include_conditional=True)
        self.assertIn("effective-address-access", {x["id"] for x in choices})
        self.assertTrue(all(x["activation"] != "after_baseline" for x in choices))
        all_rows = candidates(self.register, self.matrix, lane="release-qa",
                              include_conditional=True, include_future=True)
        self.assertIn("differential-fuzzing", {x["id"] for x in all_rows})
        gfx = candidates(self.register, self.matrix, lane="racer-hd",
                         include_conditional=True)
        self.assertIn("rider-oam-hdma", {x["id"] for x in gfx})
        self.assertNotIn("gate-cache-dependencies", {x["id"] for x in gfx})
        self.assertFalse(candidates(self.register, self.matrix, focus="definitely-not-a-source"))

    def test_routing_uses_existing_ur_and_pinned_external_paths(self):
        first = candidates(self.register, self.matrix, lane="baldosa-integration")[0]
        self.assertTrue(first["sources"]["ur"])
        self.assertTrue(first["sources"]["baldosa"] or first["sources"]["malmazuke"])
        self.assertEqual(first["priority"], "P0")

    def test_context_packet_is_bounded_and_distinguishes_blockers(self):
        text = context_hint(self.register, self.matrix, "release-qa")
        self.assertIn("WORK-QUEUE", text)
        self.assertIn("on_blocker", text)
        self.assertIn("effective-address-access", text)
        self.assertNotIn("after_baseline", text)
        self.assertLess(len(text), 2300)

    def test_bad_rows_fail_closed(self):
        base = json.loads(json.dumps(self.register))
        base["entries"].append(dict(base["entries"][0]))
        self.assertTrue(any("duplicate" in e for e in validate(base, self.matrix, self.lanes)))
        base = json.loads(json.dumps(self.register))
        base["entries"][0]["lanes"] = ["imaginary-agent"]
        self.assertTrue(any("nonexistent" in e for e in validate(base, self.matrix, self.lanes)))
        base = json.loads(json.dumps(self.register))
        base["entries"][0]["qualification"] = ""
        self.assertTrue(any("missing qualification" in e for e in validate(base, self.matrix, self.lanes)))
        base = json.loads(json.dumps(self.register))
        base["entries"][0]["id"] = "made-up-external-tool"
        self.assertTrue(any("unknown capability" in e for e in validate(base, self.matrix, self.lanes)))


if __name__ == "__main__":
    unittest.main()
