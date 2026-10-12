"""Synthetic-only diagnostics; generated handoffs are advisory not release QA."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa_adaptive_frontier as f
import qa_frontier_handoff as h


class FrontierHandoffContracts(unittest.TestCase):
    def test_handoff_preserves_real_seed_arm_source_and_no_false_gate_credit(self):
        plan=f.plan("a"*40,50000000,100)
        rows={arm:{"attempted":20,"new_bins_local":i+1}
              for i,arm in enumerate(f.ARMS)}
        data={
            "schema":f.SCHEMA,"source_sha":plan["source_sha"],
            "plan_sha256":plan["plan_sha256"],
            "disposition":"completed_observational",
            "completed_cases":100,"observed_shards":4,
            "issues":[],"release_gate_credit":0,
            "original_native_parity":False,
            "semantic_bins_observed":60,
            "strategy_summary":rows,
            "reproduction_seeds_by_fingerprint":{
                "0"*24:{"seed":50000019,"arm":"rotation","shard":0},
                "1"*24:{"seed":50000025,"arm":"balanced","shard":1},
            },
        }
        data["receipt_sha256"]=f.digest(data)
        handoff=h.report(plan,data)
        self.assertEqual(handoff["release_gate_credit"],0)
        self.assertFalse(handoff["independently_adjudicated_original_fidelity"])
        self.assertEqual(len(handoff["reproducers"]),2)
        self.assertEqual(handoff["reproducers"][0]["arm"],"rotation")
        self.assertEqual(handoff["strategies_ranked_by_within_shard_coverage"][0]["arm"],"rotation")
        md=h.markdown(handoff)
        self.assertIn("--seed 50000019 --arm rotation",md)
        self.assertIn("QA-01/07",md)
        self.assertIn("source revision",md.lower())
        with self.assertRaisesRegex(ValueError,"untrusted"):
            h.report(plan,{**data,"source_sha":"f"*40})
        wrong={**data,"release_gate_credit":1}
        wrong["receipt_sha256"]=f.digest({k:v for k,v in wrong.items()
                                          if k!="receipt_sha256"})
        with self.assertRaisesRegex(ValueError,"untrusted"):
            h.report(plan,wrong)
        missing={**data,"completed_cases":20}
        missing["receipt_sha256"]=f.digest({k:v for k,v in missing.items()
                                            if k!="receipt_sha256"})
        with self.assertRaisesRegex(ValueError,"partial"):
            h.report(plan,missing)

    def test_negative_transport_has_no_development_certification(self):
        plan=f.plan("a"*40,50000000,100)
        data={"schema":f.SCHEMA,"source_sha":plan["source_sha"],
              "plan_sha256":plan["plan_sha256"],"release_gate_credit":0,
              "original_native_parity":False,
              "disposition":"incomplete_or_failed","issues":["shard 2 missing"],
              "completed_cases":50,"observed_shards":2,
              "semantic_bins_observed":17,
              "strategy_summary":{},
              "reproduction_seeds_by_fingerprint":{}}
        data["receipt_sha256"]=f.digest(data)
        packet=h.report(plan,data)
        self.assertEqual(packet["owning_lanes"][0]["lane"],
                         "Owned native gameplay + independent CI QA")
        self.assertEqual(packet["release_gate_credit"],0)
        self.assertIn("Repair",packet["recommendation"])

    def test_rejects_invented_or_unbounded_reproduction_seed(self):
        plan=f.plan("a"*40,50000000,100)
        data={"schema":f.SCHEMA,"source_sha":plan["source_sha"],
              "plan_sha256":plan["plan_sha256"],"release_gate_credit":0,
              "original_native_parity":False,
              "disposition":"completed_observational","issues":[],
              "completed_cases":100,"observed_shards":4,
              "semantic_bins_observed":2,"strategy_summary":{},
              "reproduction_seeds_by_fingerprint":{
                  "0"*24:{"seed":99,"arm":"fake","shard":0}}}
        data["receipt_sha256"]=f.digest(data)
        with self.assertRaisesRegex(ValueError,"invalid purported"):
            h.report(plan,data)


if __name__=="__main__":
    unittest.main()
