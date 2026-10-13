"""Snapshot contracts for the accepted 2026-10-13 frontier postmortem.

These test internal consistency of the archived *research receipt*, never
native gameplay, independently calibrated SNES parity or release admission.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "analysis/data/frontier-10000-postmortem-20261013.json"
REPORT = ROOT / "docs/QA-FRONTIER-10000-POSTMORTEM-20261013.md"


class FrontierPostmortemContracts(unittest.TestCase):
    def test_source_provenance_and_exact_cardinality_are_conserved(self):
        info = json.loads(SNAPSHOT.read_text(encoding="utf8"))
        self.assertEqual(info["schema"], "ur-frontier-10000-postmortem/1")
        cohort = info["completed_run"]
        baseline = info["historical_baseline"]
        self.assertEqual(cohort["run_id"], 38306802282)
        self.assertEqual(baseline["run_id"], 38304551380)
        self.assertEqual(cohort["cases"], 10000)
        self.assertEqual(cohort["native_processes"], 11200)
        self.assertEqual(cohort["shards"] * cohort["cases_per_shard"], cohort["cases"])
        self.assertEqual(cohort["replay_and_ablation_verified_cases"], 400)
        self.assertEqual(cohort["native_processes"], cohort["cases"] +
                         3 * cohort["replay_and_ablation_verified_cases"])
        self.assertEqual(cohort["seed_range"]["last"] -
                         cohort["seed_range"]["first"] + 1, cohort["cases"])
        self.assertEqual(cohort["unique_fingerprints_prior"],
                         baseline["unique_fingerprints"])
        self.assertEqual(cohort["unique_fingerprints_prior"] +
                         cohort["exact_new_fingerprints"],
                         cohort["unique_fingerprints_cumulative"])
        self.assertEqual(cohort["unique_fingerprints_within_run"] -
                         cohort["exact_new_fingerprints"], 2)
        self.assertEqual(cohort["source_sha"], baseline["source_sha"])
        self.assertEqual(len(cohort["aggregate_object_sha256"]), 64)
        self.assertEqual(len(cohort["aggregate_receipt_sha256"]), 64)
        for name in ("original_rom_sha256", "native_executable_sha256",
                     "stock_input_sha256", "stock_script_sha256",
                     "experiment_plan_sha256"):
            self.assertRegex(cohort[name], r"^[a-f0-9]{64}$")
        self.assertEqual(info["acceptance"]["release_gate_credit"], 0)
        self.assertIs(info["acceptance"]["original_native_parity"], False)
        self.assertIs(info["acceptance"]["complete_event_verified"], False)

    def test_every_category_and_strategy_has_source_bounded_counts(self):
        info = json.loads(SNAPSHOT.read_text(encoding="utf8"))
        run = info["completed_run"]
        self.assertEqual(sum(row["attempted"] for row in
                             run["strategy_summary"].values()), run["cases"])
        self.assertEqual(set(info["negative_findings"]["strategy_arms_zero"]),
                         {k for k,v in run["strategy_summary"].items()
                          if v["attempted"] == 0})
        self.assertEqual(set(info["negative_findings"]["source_feature_categories_zero"]),
                         {k for k,v in run["source_feature_counts"].items() if v == 0})
        self.assertTrue(all(0 <= v <= run["cases"]
                            for v in run["source_feature_counts"].values()))
        self.assertEqual(set(info["first_witnesses_from_handoff"]),
                         {k for k,v in run["source_feature_counts"].items() if v > 0})
        for witness in info["first_witnesses_from_handoff"].values():
            self.assertTrue(run["seed_range"]["first"] <= witness["seed"] <=
                            run["seed_range"]["last"])
            self.assertIn(witness["arm"], run["strategy_summary"])
            self.assertTrue(0 <= witness["shard"] < run["shards"])

    def test_research_report_is_linked_and_does_not_claim_source_parity(self):
        info = json.loads(SNAPSHOT.read_text(encoding="utf8"))
        report = REPORT.read_text(encoding="utf8")
        self.assertIn(str(info["completed_run"]["run_id"]), report)
        self.assertIn(str(info["completed_run"]["exact_new_fingerprints"]), report)
        self.assertIn("0/45", report)
        self.assertIn("STRATEGY_POLICY", (ROOT / "tools/qa_adaptive_frontier.py").read_text())
        self.assertIn("fresh-five-arm-warmup-plus-decile-v1", report)


if __name__ == "__main__":
    unittest.main()
