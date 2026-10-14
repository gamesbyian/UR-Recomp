"""Resumable frontier series contracts.

Synthetic aggregates exercise ledger admission only. They are not native
guest executions, original-emulator results or gameplay observations.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa_adaptive_frontier as fr  # noqa: E402
import qa_cumulative_ledger as c  # noqa: E402
import research_yield as y  # noqa: E402
from qa_frontier_coverage import EPOCH, encode as hll_encode, observe as hll_observe  # noqa: E402
from qa_frontier_exact import encode_run  # noqa: E402

SHA = "a" * 40
DIGEST = "e" * 64
EMPTY = {"schema": c.SCHEMA, "records": []}


def synthetic_aggregate(plan: dict, exe: str = "b" * 64) -> dict:
    count = plan["frontier_cases"]
    expected = fr.plan(plan["source_sha"], plan["base_seed"], count, plan["frontier_prior"])
    shards = expected["shards"]
    # Distinct synthetic fingerprints per batch (offset by the seed window).
    prints = [format(plan["base_seed"] * 4 + i, "024x") for i in range(count * 2)]
    zero = {name: 0 for name in fr.FEATURES}
    return {
        "schema": "ur-research-frontier-2p/1", "source_sha": plan["source_sha"],
        "plan_sha256": expected["plan_sha256"], "disposition": "completed_observational",
        "release_gate_credit": 0, "issues": [], "completed_cases": count,
        "observed_shards": shards,
        "native_processes": count + 3 * shards * ((count // shards + 24) // 25),
        "semantic_bins_observed": count * 2,
        "checkpoint_unique_fingerprints": {"endurance-1740": 1, "endurance-2580": count,
                                           "endurance-3420": count},
        "identity": {"source_commit": plan["source_sha"], "native_executable_sha256": exe,
                     "rom_sha256": __import__("qa02_native_2p_seeded_endurance").ROM_SHA,
                     "stock_input_sha256": "c" * 64, "stock_script_sha256": "d" * 64},
        "source_feature_counts": dict(zero), "source_feature_reproduction_seeds": {},
        "full_trace_probe_policy": fr.TRACE_PROBE_POLICY,
        "full_trace_checkpoint_count": len(fr.ALL_FRAME_NAMES),
        "full_trace_feature_counts": dict(zero),
        "full_trace_feature_counts_by_arm": {arm: dict(zero) for arm in fr.ARMS},
        "full_trace_first_detection_frame_counts": {name: {} for name in fr.FEATURES},
        "full_trace_only_feature_counts": dict(zero),
        "full_trace_source_feature_witnesses": {}, "full_trace_only_feature_witnesses": {},
        "full_trace_raw_field_values": {name: [0] for name in fr.TRACE_RAW_FIELDS},
        "semantic_epoch": EPOCH,
        "semantic_hll_b64": hll_encode(hll_observe(prints)),
        "semantic_exact_witnesses_b64": encode_run({
            fp: (plan["base_seed"] + i // 2, "balanced", (i // 2) // (count // shards))
            for i, fp in enumerate(prints)}),
        "strategy_summary": {"balanced": {"attempted": count - 4, "new_bins_local": count - 4},
                             **{arm: {"attempted": 1, "new_bins_local": 3}
                                for arm in ("p1-focus", "p2-focus", "alternating", "rotation")}},
        "original_native_parity": False, "complete_event_verified": False,
    }


def plan_batch(ledger, run_id, series, cases=100, target=1000, digest=DIGEST):
    return c.make_plan(ledger, selected="frontier", source_sha=SHA, minutes=15,
                       windows_trials=3, run_id=run_id, frontier_cases=cases,
                       producer_digest=digest, series=series, series_target=target)


def run_batch(ledger, run_id, series, *, ok=True, cases=100, exe="b" * 64):
    p = plan_batch(ledger, run_id, series, cases=cases)
    producer = synthetic_aggregate(p, exe) if ok else None
    return c.append(ledger, p, producer, "success" if ok else "failure")


class ResumableSeries(unittest.TestCase):
    def test_batches_resume_with_fresh_seeds_until_exactly_complete(self):
        state, first = run_batch(EMPTY, 100, "new")
        self.assertEqual(first["series"]["id"], "frontier-series-100")
        seeds = {first["base_seed"]}
        for i in range(1, 10):
            state, row = run_batch(state, 100 + i, "continue")
            self.assertEqual(row["series"]["index"], i)
            seeds.add(row["base_seed"])
        self.assertEqual(len(seeds), 10)  # each batch has its own window
        status = c.series_status(state["records"])[0]
        self.assertTrue(status["complete"])
        self.assertEqual((status["completed_cases"], status["remaining_cases"]), (1000, 0))
        self.assertEqual(status["series_sha256"], c.digest(
            [r["record_sha256"] for r in state["records"]]))
        with self.assertRaises(ValueError):
            plan_batch(state, 200, "continue")  # nothing open to continue

    def test_failed_batch_consumes_its_window_and_is_never_counted(self):
        state, _ = run_batch(EMPTY, 1, "new")
        state, failed = run_batch(state, 2, "continue", ok=False)
        self.assertEqual(failed["disposition"], "incomplete_or_failed")
        state, resumed = run_batch(state, 3, "continue")
        self.assertEqual(resumed["series"]["index"], 2)
        self.assertNotEqual(resumed["base_seed"], failed["base_seed"])
        status = c.series_status(state["records"])[0]
        self.assertEqual(status["completed_cases"], 200)
        self.assertEqual(status["failed_batches"], [2])
        self.assertFalse(status["complete"])

    def test_series_pins_arm_prior_despite_adaptive_learning(self):
        state, first = run_batch(EMPTY, 1, "new")
        state, _ = run_batch(state, 2, "continue")
        adaptive = c.frontier_strategy_prior(state)
        nxt = plan_batch(state, 3, "continue")
        self.assertEqual(nxt["frontier_prior"], first["series"]["frontier_prior"])
        free = plan_batch(state, 3, "none")
        self.assertEqual(free["frontier_prior"], adaptive)

    def test_changed_producer_or_oversized_batch_is_refused(self):
        state, _ = run_batch(EMPTY, 1, "new")
        with self.assertRaises(ValueError):
            plan_batch(state, 2, "continue", digest="f" * 64)
        with self.assertRaises(ValueError):
            plan_batch(state, 2, "continue", cases=1000)  # only 900 remain
        with self.assertRaises(ValueError):
            plan_batch(EMPTY, 2, "new", cases=1000, target=1000)
        with self.assertRaises(ValueError):
            c.make_plan(EMPTY, selected="windows", source_sha=SHA, minutes=15,
                        windows_trials=3, run_id=9, producer_digest=DIGEST, series="new",
                        series_target=1000)

    def test_tampered_series_rows_are_rejected(self):
        state, _ = run_batch(EMPTY, 1, "new")
        state, second = run_batch(state, 2, "continue")
        for field, value in (("index", 5), ("target_cases", 10000), ("frontier_prior", {})):
            forged_row = {**second, "series": {**second["series"], field: value}}
            forged_row["record_sha256"] = c.digest(
                {k: v for k, v in forged_row.items() if k != "record_sha256"})
            with self.subTest(field=field), self.assertRaises(ValueError):
                c.validate_ledger({**state, "records": [state["records"][0], forged_row]})

    def test_binary_change_is_reported_as_a_split_cohort(self):
        state, _ = run_batch(EMPTY, 1, "new", exe="b" * 64)
        state, _ = run_batch(state, 2, "continue", exe="9" * 64)
        status = c.series_status(state["records"])[0]
        self.assertFalse(status["single_binary_cohort"])
        self.assertEqual(len(status["native_executables"]), 2)

    def test_yield_view_reports_series_progress(self):
        state, _ = run_batch(EMPTY, 1, "new")
        report = y.build_report(state)
        self.assertEqual(report["series"][0]["completed_cases"], 100)
        self.assertIn("frontier-series-1", y.markdown(report))


class CoordinatorSeriesContract(unittest.TestCase):
    def test_series_is_explicit_and_forwarded_to_reservation(self):
        text = (ROOT / ".github/workflows/qa-cumulative-research.yml").read_text()
        self.assertIn("frontier_series:", text)
        self.assertIn("options: [none, new-1000, new-10000, continue]", text)
        self.assertIn('--series "$SERIES_MODE" --series-target "$SERIES_TARGET"', text)


class WitnessBinaryRetention(unittest.TestCase):
    def test_frontier_keeps_its_exact_native_binary_as_long_as_witness_handoffs(self):
        wf = (ROOT / ".github/workflows/qa-adaptive-frontier.yml").read_text()
        step = wf.split("Retain exact witness native binary", 1)[1].split("- name:", 1)[0]
        self.assertIn("name: qa-frontier-witness-native", step)
        self.assertIn("retention-days: 90", step)
        # Never longer-lived than needed, never the ROM.
        self.assertNotIn(".sfc", step)


if __name__ == "__main__":
    unittest.main()
