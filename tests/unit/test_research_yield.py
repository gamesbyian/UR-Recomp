"""Synthetic yield-rule contracts. Fixture rows are ledger-shaped inputs, not
native, original-emulator or gameplay outcomes."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import research_yield as y  # noqa: E402

FEATURES = ("both-air-raw", "both-moving-raw", "offscreen-register-nonzero")


def frontier(run_id, cases, air=0, observer=None, per_case_new=2.0, usage=None):
    metrics = {"cases": cases, "exact_new_unique_fingerprints": int(per_case_new * cases),
               "checkpoint_unique_fingerprints": {"a": 1, "b": cases, "c": cases}}
    counts = {"both-air-raw": air, "both-moving-raw": cases, "offscreen-register-nonzero": 0}
    if observer:
        metrics["full_trace_probe_policy"] = observer
        metrics["full_trace_feature_counts"] = counts
        if air:
            metrics["full_trace_source_feature_witnesses"] = {
                "both-air-raw": {"seed": 77, "arm": "rotation", "first_frame": 2580, "shard": 0}}
    else:
        metrics["source_feature_counts"] = counts
    row = {"campaign": "frontier", "origin": "coordinator", "disposition": "completed_positive",
           "github_run_id": run_id, "metrics": metrics}
    if usage is not None:
        row["runner_usage"] = {"total_runner_minutes": usage}
    return row


def lane(name, disposition="completed_positive", obs=100, run_id=1, reason=None):
    metrics = {"cases": obs, "observations": obs} if disposition != "incomplete_or_failed" else {
        "reason": reason or "x", "reusable_job_result": "cancelled"}
    return {"campaign": name, "origin": "coordinator", "disposition": disposition,
            "github_run_id": run_id, "metrics": metrics}


class Bounds(unittest.TestCase):
    def test_rule_of_three(self):
        self.assertIsNone(y.rule_of_three(0))
        self.assertAlmostEqual(y.rule_of_three(300), 0.01)
        self.assertEqual(y.cases_to_bound(0.001), 3000)


class FrontierYield(unittest.TestCase):
    def test_non_saturating_census_is_never_a_reason_to_run(self):
        report = y.build_report({"records": [frontier(1, 100), frontier(2, 10000)]})
        self.assertTrue(report["frontier"]["fingerprint_census_non_saturating"])
        rec = report["frontier_default_recommendation"]
        self.assertEqual(rec["next"], "none")
        self.assertIn("non-saturating", rec["reason"])

    def test_saturating_census_is_not_mislabelled(self):
        report = y.build_report({"records": [frontier(1, 100, per_case_new=0.3)]})
        self.assertFalse(report["frontier"]["fingerprint_census_non_saturating"])

    def test_first_occurrence_and_absence_bound(self):
        report = y.build_report({"records": [frontier(1, 1000), frontier(2, 100, air=1, observer="v2")]})
        feats = report["frontier"]["features"]
        self.assertEqual(feats["both-air-raw"]["first_occurrence"]["seed"], 77)
        self.assertEqual(feats["both-air-raw"]["first_occurrence"]["github_run_id"], 2)
        self.assertTrue(feats["both-air-raw"]["rare"])
        self.assertAlmostEqual(feats["offscreen-register-nonzero"]["zero_incidence_95pct_upper_bound"],
                               3 / 1100)
        self.assertIn("both-moving-raw", report["frontier"]["uninformative_features"])

    def test_rare_witness_means_reproduce_not_volume(self):
        report = y.build_report({"records": [frontier(1, 10000), frontier(2, 100, air=1, observer="v2")]})
        rec = y.frontier_recommendation(report["frontier"], target_feature="both-air-raw")
        self.assertEqual((rec["next"], rec["action"]), ("none", "reproduce_witness"))
        self.assertEqual(rec["witness"]["seed"], 77)

    def test_rate_estimates_use_only_the_latest_observer_cohort(self):
        # The pooled 10,100 cases mix a starved policy; the rate question
        # restarts at the 100-case current cohort and asks for 1,000, not 10,000.
        report = y.build_report({"records": [frontier(1, 10000), frontier(2, 100, air=1, observer="v2")]})
        self.assertEqual(report["frontier"]["latest_cohort"]["github_run_ids"], [2])
        rec = y.frontier_recommendation(report["frontier"], target_feature="both-air-raw",
                                        needs_rate=True)
        self.assertEqual(rec["next"], "1000")
        big = y.build_report({"records": [frontier(i, 1000, air=1 if i == 3 else 0, observer="v2")
                                          for i in range(1, 4)]})
        self.assertEqual(y.frontier_recommendation(big["frontier"], target_feature="both-air-raw",
                                                   needs_rate=True)["next"], "10000")

    def test_absence_needs_a_threshold_and_stops_once_bounded(self):
        report = y.build_report({"records": [frontier(1, 10000)]})
        feat = "offscreen-register-nonzero"
        self.assertEqual(y.frontier_recommendation(report["frontier"], target_feature=feat)["next"], "none")
        done = y.frontier_recommendation(report["frontier"], target_feature=feat, consumer_threshold=0.001)
        self.assertEqual(done["next"], "none")
        more = y.frontier_recommendation(report["frontier"], target_feature=feat, consumer_threshold=0.0001)
        self.assertEqual(more["next"], "10000")
        self.assertEqual(more["additional_cases_needed"], 20000)

    def test_observer_change_gets_a_100_case_pilot_only(self):
        report = y.build_report({"records": []})
        self.assertEqual(y.frontier_recommendation(report["frontier"], observer_changed=True)["next"], "100")

    def test_cost_per_case_when_usage_recorded(self):
        report = y.build_report({"records": [frontier(1, 100, usage=42.0), frontier(2, 100)]})
        runs = report["frontier"]["runs"]
        self.assertEqual((runs[0]["runner_minutes_per_case"], runs[1]["runner_minutes_per_case"]),
                         (0.42, None))


class ArmReward(unittest.TestCase):
    def test_flat_fingerprint_reward_is_detected(self):
        rows = [frontier(1, 100), frontier(2, 100)]
        for row in rows:
            row["metrics"]["strategy_summary"] = {
                "balanced": {"attempted": 50, "new_bins_local": 100},
                "rotation": {"attempted": 50, "new_bins_local": 105}}
        reward = y.build_report({"records": rows})["frontier"]["arm_reward"]
        self.assertTrue(reward["flat"])
        self.assertIn("Arm reward is flat", y.markdown(y.build_report({"records": rows})))

    def test_informative_reward_and_starvation(self):
        row = frontier(1, 100)
        row["metrics"]["strategy_summary"] = {
            "balanced": {"attempted": 60, "new_bins_local": 60},
            "rotation": {"attempted": 40, "new_bins_local": 120},
            "alternating": {"attempted": 0, "new_bins_local": 0}}
        reward = y.build_report({"records": [row]})["frontier"]["arm_reward"]
        self.assertFalse(reward["flat"])
        self.assertEqual(reward["starved_arms"], ["alternating"])


class DurabilityYield(unittest.TestCase):
    def test_failures_are_listed_and_never_counted_as_observations(self):
        report = y.build_report({"records": [
            lane("windows", obs=120, run_id=1),
            lane("windows", "incomplete_or_failed", run_id=2, reason="cancel"),
            lane("original-native", "strict_divergence", obs=3, run_id=3)]})
        w = report["durability"]["windows"]
        self.assertEqual((w["runs"], w["positive_runs"], w["failed_runs"], w["observations"]),
                         (2, 1, 1, 120))
        self.assertAlmostEqual(w["zero_failure_95pct_upper_bound_per_observation"], 0.025)
        self.assertEqual(w["failure_reasons"][0]["reusable_job_result"], "cancelled")
        # A strict divergence is evidence, but never a durability bound.
        o = report["durability"]["original-native"]
        self.assertEqual(o["strict_divergence_runs"], 1)
        self.assertIsNone(o["zero_failure_95pct_upper_bound_per_observation"])
        self.assertEqual(report["release_gate_credit"], 0)

    def test_markdown_renders_every_lane(self):
        text = y.markdown(y.build_report({"records": [frontier(1, 100), lane("windows")]}))
        self.assertIn("non-saturating", text)
        self.assertIn("| windows |", text)


class CoordinatorPublishesYield(unittest.TestCase):
    def test_yield_view_is_read_only_and_cannot_block_the_writer(self):
        text = (ROOT / ".github/workflows/qa-cumulative-research.yml").read_text()
        step = text.split("Publish derived cumulative yield view", 1)[1].split("- name:", 1)[0]
        self.assertIn("continue-on-error: true", step)
        self.assertNotIn("--out research-evidence", step)
        self.assertLess(text.index("git push origin HEAD:refs/heads/research/qa-cumulative-ledger"),
                        text.index("Publish derived cumulative yield view"))


if __name__ == "__main__":
    unittest.main()
