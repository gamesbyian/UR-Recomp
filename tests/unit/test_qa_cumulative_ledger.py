"""Offline contracts only: ledger reservations never assert real game outcomes."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tools"))
import qa_cumulative_ledger as c

SHA="a"*40
LEDGER={"schema":c.SCHEMA,"records":[]}


def native_report():
    return {
        "schema":"ur-native-2p-input-endurance/1","source_commit":SHA,
        "disposition":"completed_positive","release_gate_credit":0,
        "observed_shards":2,"total_unique_cases":12,
        "total_real_native_processes":48,"issues":[],
    }


def make(l=None,selected="native-2p",run_id=10):
    return c.make_plan(l or LEDGER,selected=selected,source_sha=SHA,
                       minutes=15,windows_trials=3,run_id=run_id)


class CumulativeLedgerContracts(unittest.TestCase):
    def test_exact_build_and_nonoverlapping_reproducible_seed_reservations(self):
        state=LEDGER
        for i in range(100):
            plan=make(state,run_id=i+10)
            self.assertEqual(plan["base_seed"], c.BASE+i*c.WINDOW)
            state,_=c.append(state,plan,native_report(),"success")
        c.validate_ledger(state)
        self.assertEqual(len(state["records"]),100)
        self.assertEqual(len({r["base_seed"] for r in state["records"]}),100)
        self.assertEqual(sum(r["metrics"]["cases"] for r in state["records"]),1200)
        self.assertEqual(sum(r["metrics"]["observations"] for r in state["records"]),4800)
        self.assertEqual(sum(r["release_gate_credit"] for r in state["records"]),0)

    def test_native_cross_shard_seed_intervals_are_disjoint_across_run_sequences(self):
        # Source fixture seeds: base + shard*1,000,003 + case_index
        # (case_index 0..2999). This proves no later run's shard can reuse
        # the other shard's cases even after hundreds of reservations.
        self.assertGreaterEqual(c.WINDOW,3000)
        remainder=1000003 % c.WINDOW
        self.assertGreater(min(remainder,c.WINDOW-remainder),2999)
        last_base=c.BASE+c.MAX_SEQUENCE*c.WINDOW
        self.assertLessEqual(last_base+1000003+2999,99999999)
        self.assertGreater(c.BASE,20261011)

    def test_failure_consumes_seed_and_remains_auditable(self):
        p=make()
        newer,failed=c.append(LEDGER,p,None,"failure")
        self.assertEqual(failed["disposition"],"incomplete_or_failed")
        self.assertEqual(failed["metrics"]["cases"] if "cases" in failed["metrics"] else 0,0)
        second=make(newer,run_id=11)
        self.assertEqual(second["sequence"],1)
        self.assertEqual(second["base_seed"],p["base_seed"]+c.WINDOW)
        self.assertNotEqual(second["base_seed"],p["base_seed"])

    def test_tampering_and_stale_plan_are_never_silently_accepted(self):
        p=make()
        state,_=c.append(LEDGER,p,native_report(),"success")
        with self.assertRaisesRegex(ValueError,"ledger changed"):
            c.append(state,p,native_report(),"success")
        evil={**p,"base_seed":p["base_seed"]+1}
        with self.assertRaisesRegex(ValueError,"tampered"):
            c.append(LEDGER,evil,native_report(),"success")
        modified=json.loads(json.dumps(state))
        modified["records"][0]["metrics"]["cases"]=99999
        with self.assertRaisesRegex(ValueError,"signature"):
            c.validate_ledger(modified)
        with self.assertRaisesRegex(ValueError,"already recorded"):
            make(state,run_id=10)

    def test_original_native_divergence_is_recorded_without_fabricated_acceptance(self):
        p=make(selected="original-native")
        report={
            "schema":"ur-qa01-event-campaign/1","source_sha":SHA,
            "transport_complete":True,"release_admissions":0,
            "counts":{"strict_divergence":3,"strict_candidate":0,
                      "missing_evidence":0,"producer_error":0},
            "selected_cases":3,"completed":3,
        }
        state,row=c.append(LEDGER,p,report,"success")
        self.assertEqual(row["disposition"],"strict_divergence")
        self.assertEqual(row["release_gate_credit"],0)
        self.assertEqual(row["metrics"]["cases"],3)
        self.assertEqual(row["metrics"]["observations"],3)
        self.assertEqual(state["records"][0]["origin"],"coordinator")

    def test_source_rejection_and_incomplete_population(self):
        p=make()
        for report,reason in (
            ({**native_report(),"source_commit":"b"*40},"exact planned"),
            ({**native_report(),"total_real_native_processes":100},"process counts"),
            ({**native_report(),"release_gate_credit":1},"release"),
        ):
            with self.subTest(reason=reason):
                state,record=c.append(LEDGER,p,report,"success")
                self.assertEqual(record["disposition"],"incomplete_or_failed")
                self.assertIn(reason,record["metrics"]["reason"])
                self.assertEqual(state["records"][0]["base_seed"],p["base_seed"])
                self.assertEqual(record["release_gate_credit"],0)
        state,row=c.append(LEDGER,p,{**native_report(),"disposition":"incomplete_or_failed"},"success")
        self.assertEqual(row["disposition"],"incomplete_or_failed")
        self.assertEqual(row["release_gate_credit"],0)

    def test_round_robin_is_bounded_across_all_seven_research_families(self):
        state=LEDGER
        sequence=[]
        for index,campaign in enumerate(c.CAMPAIGNS):
            p=make(state,selected="auto",run_id=100+index)
            self.assertEqual(p["campaign"],campaign)
            sequence.append(campaign)
            state,_=c.append(state,p,None,"failure")
        self.assertEqual(tuple(sequence),c.CAMPAIGNS)
        self.assertEqual(make(state,selected="auto",run_id=120)["campaign"],c.CAMPAIGNS[0])

    def test_strict_windows_fault_and_perf_aggregate_semantics(self):
        for campaign,extra,units in (
            ("windows",{"schema":"ur-baldosa-win32-reliability-batch/1",
                        "source_commit":SHA,"passed_trials":12,"attempted_trials":12,
                        "observed_shards":4},12),
            ("fault-recovery",{"schema":"ur-qa02-seeded-fault-endurance/1",
                               "source_sha":SHA,"completed_unique_timing_batches":20,
                               "completed_real_fault_process_journeys":200,
                               "observed_suites":5},200),
            ("performance",{"schema":"ur-cumulative-performance/1",
                            "source_sha":SHA,"completed_processes":2,
                            "sampled_process_seconds":130},130),
            ("graphics",{"schema":"ur-cumulative-graphics/1",
                         "source_sha":SHA,"unique_seeded_frame_sweeps":5,
                         "measured_frame_checks":25000},25000),
        ):
            with self.subTest(campaign=campaign):
                p=make(selected=campaign)
                row={**extra,"disposition":"completed_positive",
                     "release_gate_credit":0,"issues":[]}
                _,record=c.append(LEDGER,p,row,"success")
                self.assertEqual(record["metrics"]["observations"],units)
                self.assertEqual(record["release_gate_credit"],0)

    def test_10k_frontier_uses_real_source_plan_and_retains_novelty_without_release_credit(self):
        from qa_adaptive_frontier import plan as source_plan
        from qa_frontier_coverage import EPOCH, observe as coverage_observe, encode as coverage_encode
        from qa_frontier_exact import encode_run as encode_exact
        for count,shards in ((100,4),(1000,10),(10000,40)):
            with self.subTest(count=count):
                p=c.make_plan(LEDGER,selected="frontier",
                              source_sha=SHA,minutes=15,windows_trials=3,
                              frontier_cases=count,run_id=123)
                expected=source_plan(SHA,p["base_seed"],count)
                observed={
                    "schema":"ur-research-frontier-2p/1",
                    "source_sha":SHA,"plan_sha256":expected["plan_sha256"],
                    "disposition":"completed_observational",
                    "release_gate_credit":0,"issues":[],
                    "completed_cases":count,"observed_shards":shards,
                    "native_processes":count+3*shards*((count//shards+24)//25),
                    "semantic_bins_observed":count*2,
                    "checkpoint_unique_fingerprints":{
                        "endurance-1740":1,"endurance-2580":count,
                        "endurance-3420":count},
                    "identity":{
                        "source_commit":p["source_sha"],
                        "native_executable_sha256":"b"*64,
                        "rom_sha256":__import__("qa02_native_2p_seeded_endurance").ROM_SHA,
                        "stock_input_sha256":"c"*64,
                        "stock_script_sha256":"d"*64,
                    },
                    "source_feature_counts":{name:0 for name in __import__("qa_adaptive_frontier").FEATURES},
                    "source_feature_reproduction_seeds":{},
                    "full_trace_probe_policy":"full-existing-15-wram-frames-raw-fields-v1",
                    "full_trace_checkpoint_count":15,
                    "full_trace_feature_counts":{name:0 for name in __import__("qa_adaptive_frontier").FEATURES},
                    "full_trace_feature_counts_by_arm":{
                        arm:{name:0 for name in __import__("qa_adaptive_frontier").FEATURES}
                        for arm in __import__("qa_adaptive_frontier").ARMS},
                    "full_trace_first_detection_frame_counts":{
                        name:{} for name in __import__("qa_adaptive_frontier").FEATURES},
                    "full_trace_only_feature_counts":{name:0 for name in __import__("qa_adaptive_frontier").FEATURES},
                    "full_trace_source_feature_witnesses":{},
                    "full_trace_only_feature_witnesses":{},
                    "full_trace_raw_field_values":{name:[0] for name in __import__("qa_adaptive_frontier").TRACE_RAW_FIELDS},
                    "semantic_epoch":EPOCH,
                    "semantic_hll_b64":coverage_encode(coverage_observe(
                        [format(i,"024x") for i in range(count*2)])),
                    "semantic_exact_witnesses_b64":encode_exact({
                        format(i,"024x"): (
                            p["base_seed"]+i//2,"balanced",
                            (i//2)//(count//shards))
                        for i in range(count*2)}),
                    "strategy_summary":{
                        "balanced":{"attempted":count-4,"new_bins_local":count-4},
                        "p1-focus":{"attempted":1,"new_bins_local":3},
                        "p2-focus":{"attempted":1,"new_bins_local":3},
                        "alternating":{"attempted":1,"new_bins_local":3},
                        "rotation":{"attempted":1,"new_bins_local":3},
                    },
                    "original_native_parity":False,
                    "complete_event_verified":False,
                }
                new,record=c.append(LEDGER,p,observed,"success")
                self.assertEqual(record["disposition"],"completed_positive")
                self.assertEqual(record["metrics"]["cases"],count)
                self.assertEqual(record["metrics"]["semantic_bins_observed"],count*2)
                self.assertEqual(record["metrics"]["strategy_summary"],observed["strategy_summary"])
                self.assertEqual(record["metrics"]["full_trace_checkpoint_count"],15)
                self.assertEqual(record["metrics"]["full_trace_feature_counts_by_arm"],
                                 observed["full_trace_feature_counts_by_arm"])
                self.assertEqual(record["metrics"]["full_trace_first_detection_frame_counts"],
                                 observed["full_trace_first_detection_frame_counts"])
                self.assertEqual(record["metrics"]["full_trace_feature_counts"],
                                 observed["full_trace_feature_counts"])
                self.assertEqual(record["metrics"]["full_trace_raw_field_values"],
                                 observed["full_trace_raw_field_values"])
                self.assertGreaterEqual(record["metrics"]["estimated_post_unique_bins"],1)
                self.assertTrue(record["metrics"]["approximate_not_an_exact_new_case_count"])
                self.assertEqual(record["metrics"]["exact_new_unique_fingerprints"],count*2)
                self.assertEqual(new["frontier_exact_coverage"]["exact_unique_observed_fingerprints"],count*2)
                self.assertIn("frontier_coverage",new)
                self.assertEqual(new["frontier_coverage"]["real_cases_observed"],count)
                self.assertEqual(record["frontier_cases"],count)
                self.assertEqual(record["release_gate_credit"],0)
                self.assertEqual(len(new["records"]),1)
                broken={**observed,"native_processes":count}
                _,rejected=c.append(LEDGER,p,broken,"success")
                self.assertEqual(rejected["disposition"],"incomplete_or_failed")
                changed={
                    **observed,
                    "checkpoint_unique_fingerprints":{
                        **observed["checkpoint_unique_fingerprints"],
                        "endurance-1740":0,
                    }
                }
                _,rejected_checkpoint=c.append(LEDGER,p,changed,"success")
                self.assertEqual(rejected_checkpoint["disposition"],"incomplete_or_failed")
                self.assertNotIn("frontier_exact_coverage", _)
                for key,bad in (
                    ("full_trace_checkpoint_count",3),
                    ("full_trace_feature_counts_by_arm",{"balanced":{}}),
                    ("full_trace_first_detection_frame_counts",{"both-air-raw":{"1740":1}}),
                    ("full_trace_probe_policy","unknown-trace"),
                    ("full_trace_feature_counts",{"both-air-raw":1}),
                    ("full_trace_raw_field_values",{"split":[1,1]}),
                    ("full_trace_only_feature_witnesses",{"both-air-raw":{
                        "seed":p["base_seed"],"arm":"balanced",
                        "shard":0,"first_frame":1860}}),
                ):
                    with self.subTest(field=key):
                        _,rejected_probe=c.append(LEDGER,p,{**observed,key:bad},"success")
                        self.assertEqual(rejected_probe["disposition"],"incomplete_or_failed")
                        self.assertNotIn("frontier_exact_coverage",_)


    def test_no_unbounded_or_forged_source_requests(self):
        for n in (0,121,10000):
            with self.subTest(n=n),self.assertRaises(ValueError):
                c.make_plan(LEDGER,selected="native-2p",source_sha=SHA,
                            minutes=n,windows_trials=3,run_id=10)
        with self.assertRaises(ValueError):
            c.make_plan(LEDGER,selected="unknown",source_sha=SHA,
                        minutes=15,windows_trials=3,run_id=10)


if __name__=="__main__":
    unittest.main()
