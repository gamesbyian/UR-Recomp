"""Synthetic-only checks for approximate cross-run state coverage.

These never execute a native guest or establish original-SNES correctness.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa_frontier_coverage as c
import qa_cumulative_ledger as ledger


def tokens(start:int,n:int)->list[str]:
    return [format(i,"024x") for i in range(start,start+n)]


class FrontierCoverageContracts(unittest.TestCase):
    def test_empty_duplicate_and_cross_run_union_are_monotone(self):
        blank=c.empty()
        self.assertEqual(len(blank),4096)
        self.assertEqual(c.estimate(blank),0)
        a=c.observe(tokens(0,1000))
        b=c.observe(tokens(500,1000))
        prior=c.estimate(a)
        self.assertAlmostEqual(prior,1000,delta=150)
        unchanged=c.union(a,a)
        self.assertEqual(unchanged,a)
        merged=c.union(a,b)
        self.assertGreaterEqual(c.estimate(merged),c.estimate(a))
        self.assertAlmostEqual(c.estimate(merged),1500,delta=225)
        self.assertEqual(c.decode(c.encode(merged)),merged)

    def test_source_corpus_repeated_population_estimates_no_new_states(self):
        first=c.observe(tokens(0,2500))
        record,delta=c.make_record(None,first,1000)
        c.validate_record(record)
        self.assertEqual(record["real_cases_observed"],1000)
        self.assertTrue(delta["approximate_not_an_exact_new_case_count"])
        self.assertGreater(delta["estimated_new_unique_bins"],1800)
        repeat,second=c.make_record(record,first,1000)
        self.assertEqual(repeat["estimated_unique_normalized_states"],
                         record["estimated_unique_normalized_states"])
        self.assertEqual(second["estimated_new_unique_bins"],0)
        self.assertEqual(repeat["real_cases_observed"],2000)
        different,new=c.make_record(repeat,c.observe(tokens(2500,1800)),1000)
        self.assertGreater(new["estimated_post_unique_bins"],
                           second["estimated_post_unique_bins"])
        self.assertEqual(different["updates"],3)
        self.assertEqual(different["release_gate_credit"],0)

    def test_modified_sample_and_forged_oracle_are_rejected(self):
        src=c.observe(tokens(100,100))
        record,_=c.make_record(None,src,100)
        for mode in ("signature","estimated_count","credit","original","epoch","register"):
            with self.subTest(mode=mode):
                mod=json.loads(json.dumps(record))
                if mode=="signature":mod["record_sha256"]="f"*64
                if mode=="estimated_count":mod["estimated_unique_normalized_states"]=99999
                if mode=="credit":mod["release_gate_credit"]=1
                if mode=="original":mod["original_native_parity_claimed"]=True
                if mode=="epoch":mod["semantic_epoch"]="invented-v2"
                if mode=="register":mod["registers_b64"]="AAA!"
                with self.assertRaises(ValueError):
                    c.validate_record(mod)

    def test_bounded_and_semantically_grounded_state_inputs(self):
        for invalid in ("not_hex24","F"*24,"0"*23,"0"*25):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                c.observe([invalid])
        with self.assertRaises(ValueError):
            c.observe(tokens(0,30001))
        with self.assertRaises(ValueError):
            c.make_record(None,c.empty(),0)
        with self.assertRaises(ValueError):
            c.decode(c.encode(c.empty())[:-1])
        with self.assertRaises(ValueError):
            c.validate(bytes([255])*4096)
        matched=c.observe(tokens(0,140))
        report={"semantic_epoch":c.EPOCH,"semantic_hll_b64":c.encode(matched),
                "semantic_bins_observed":140}
        self.assertEqual(c.observed_report(report),matched)
        with self.assertRaises(ValueError):
            c.observed_report({**report,"semantic_bins_observed":3000})
        with self.assertRaises(ValueError):
            c.observed_report({**report,"semantic_epoch":"changed-fields-v2"})

    def test_ledger_cumulative_reused_states_not_new_discovery(self):
        from qa_adaptive_frontier import plan as original_plan
        source="a"*40
        data={"schema":ledger.SCHEMA,"records":[]}
        samples=c.observe(tokens(0,100))
        for run_id in (10,11):
            plan=ledger.make_plan(
                data,selected="frontier",source_sha=source,
                minutes=15,windows_trials=3,frontier_cases=100,run_id=run_id)
            original=original_plan(
                source,plan["base_seed"],100,plan["frontier_prior"])
            producer={
                "schema":"ur-research-frontier-2p/1","source_sha":source,
                "plan_sha256":original["plan_sha256"],"release_gate_credit":0,
                "disposition":"completed_observational","completed_cases":100,
                "native_processes":112,"observed_shards":4,
                "semantic_bins_observed":100,"semantic_epoch":c.EPOCH,
                "semantic_hll_b64":c.encode(samples),
                "strategy_summary":{
                    "balanced":{"attempted":100,"new_bins_local":100},
                    "p1-focus":{"attempted":0,"new_bins_local":0},
                    "p2-focus":{"attempted":0,"new_bins_local":0},
                    "alternating":{"attempted":0,"new_bins_local":0},
                    "rotation":{"attempted":0,"new_bins_local":0},
                },
                "original_native_parity":False,"complete_event_verified":False,
                "issues":[]
            }
            data,row=ledger.append(data,plan,producer,"success")
            self.assertEqual(row["disposition"],"completed_positive")
            if run_id==11:
                self.assertEqual(row["metrics"]["estimated_new_unique_bins"],0)
        ledger.validate_ledger(data)
        self.assertEqual(data["frontier_coverage"]["updates"],2)
        self.assertEqual(data["frontier_coverage"]["real_cases_observed"],200)

    def test_failed_campaign_consumes_seed_but_keeps_observed_corpus_unchanged(self):
        data={"schema":ledger.SCHEMA,"records":[]}
        plan=ledger.make_plan(data,selected="frontier",source_sha="a"*40,
                              minutes=15,windows_trials=3,
                              frontier_cases=100,run_id=99)
        newer,failed=ledger.append(data,plan,None,"failure")
        self.assertEqual(failed["disposition"],"incomplete_or_failed")
        self.assertNotIn("frontier_coverage",newer)
        self.assertEqual(ledger.next_seed(newer,"frontier")[0],1)
        self.assertEqual(failed["release_gate_credit"],0)


if __name__=="__main__":
    unittest.main()
