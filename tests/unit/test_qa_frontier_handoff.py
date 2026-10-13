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
            "source_feature_counts":{
                name:(3 if name=="both-air-raw" else
                      2 if name=="checkpoint-pointer-changes" else 0)
                for name in f.FEATURES
            },
            "source_feature_reproduction_seeds":{
                "both-air-raw":{"seed":50000019,"arm":"rotation","shard":0},
                "checkpoint-pointer-changes":{"seed":50000025,"arm":"balanced","shard":1},
            },
            "dense_observer_epoch":f.DENSE_EPOCH,
            "dense_feature_counts":{
                name:(3 if name=="both-air-raw" else
                      2 if name=="checkpoint-pointer-changes" else
                      1 if name=="offscreen-register-nonzero" else 0)
                for name in f.FEATURES
            },
            "dense_feature_reproduction_seeds":{
                "both-air-raw":{"seed":50000019,"arm":"rotation","shard":0,
                                 "first_frame":"endurance-1860"},
                "checkpoint-pointer-changes":{"seed":50000025,"arm":"balanced",
                                               "shard":1,"first_frame":"endurance-2580"},
                "offscreen-register-nonzero":{"seed":50000036,"arm":"p1-focus",
                                               "shard":1,"first_frame":"endurance-1980"}
            },
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
        self.assertEqual(len(handoff["source_feature_reproducers"]),2)
        self.assertEqual(len(handoff["dense_feature_reproducers"]),3)
        self.assertTrue(any(
            w["newly_visible_at_dense_cadence"] and
            w["feature"]=="offscreen-register-nonzero" and
            w["first_frame"]=="endurance-1980"
            for w in handoff["dense_feature_reproducers"]))
        self.assertIn("seed 50000036",handoff["owning_lanes"][1]["next_proof"])

        self.assertEqual(handoff["source_feature_reproducers"][0]["feature"],"checkpoint-pointer-changes")
        self.assertIn("seed 50000025",handoff["owning_lanes"][0]["next_proof"])
        self.assertIn("seed 50000019",handoff["owning_lanes"][1]["next_proof"])
        self.assertEqual(handoff["strategies_ranked_by_within_shard_coverage"][0]["arm"],"rotation")
        md=h.markdown(handoff)
        self.assertIn("--seed 50000019 --arm rotation",md)
        self.assertIn("Fifteen-frame raw-observer findings",md)
        self.assertIn("endurance-1980",md)
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

    def test_invalid_or_forged_source_category_never_becomes_owner_direction(self):
        plan=f.plan("a"*40,50000000,100)
        def source_report():
            row={
                "schema":f.SCHEMA,"source_sha":plan["source_sha"],
                "plan_sha256":plan["plan_sha256"],
                "disposition":"completed_observational",
                "completed_cases":100,"observed_shards":4,
                "issues":[],"release_gate_credit":0,
                "original_native_parity":False,"semantic_bins_observed":20,
                "strategy_summary":{},
                "reproduction_seeds_by_fingerprint":{},
                "source_feature_counts":{name:0 for name in f.FEATURES},
                "source_feature_reproduction_seeds":{},
            }
            row["receipt_sha256"]=f.digest(row)
            return row
        for scenario in ("count","missing","wrong-seed","fake-feature","zero-with-repro"):
            with self.subTest(scenario=scenario):
                row=source_report()
                if scenario=="count":
                    row["source_feature_counts"]["both-air-raw"]=101
                elif scenario=="missing":
                    row.pop("source_feature_counts")
                elif scenario=="wrong-seed":
                    row["source_feature_counts"]["both-air-raw"]=1
                    row["source_feature_reproduction_seeds"]["both-air-raw"]={
                        "seed":9,"arm":"balanced","shard":0}
                elif scenario=="fake-feature":
                    row["source_feature_counts"]["invented-renderer-correct"]=1
                elif scenario=="zero-with-repro":
                    row["source_feature_reproduction_seeds"]["both-air-raw"]={
                        "seed":50000001,"arm":"balanced","shard":0}
                row["receipt_sha256"]=f.digest({k:v for k,v in row.items()
                                                 if k!="receipt_sha256"})
                with self.assertRaises(ValueError):
                    h.report(plan,row)

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
              "source_feature_counts":{name:0 for name in f.FEATURES},
              "source_feature_reproduction_seeds":{},
              "reproduction_seeds_by_fingerprint":{
                  "0"*24:{"seed":99,"arm":"fake","shard":0}}}
        data["receipt_sha256"]=f.digest(data)
        with self.assertRaisesRegex(ValueError,"invalid purported"):
            h.report(plan,data)


if __name__=="__main__":
    unittest.main()
