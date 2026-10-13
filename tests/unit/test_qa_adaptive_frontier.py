"""Synthetic contracts; never a real guest gameplay witness."""
from __future__ import annotations
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa_adaptive_frontier as f

SOURCE="a"*40


def report_tree(root: Path, count: int = 100) -> tuple[dict,Path]:
    p=f.plan(SOURCE,50000000,count)
    receipts=root/"receipts"
    receipts.mkdir()
    ident={
        "source_commit":SOURCE,"native_executable_sha256":"b"*64,
        "rom_sha256":f.guest.ROM_SHA,"stock_input_sha256":"c"*64,
        "stock_script_sha256":"d"*64,
    }
    for shard in range(p["shards"]):
        attempts=dict.fromkeys(f.ARMS,0)
        gains=dict.fromkeys(f.ARMS,0)
        rows=[]
        tokens=set()
        _,n=f.assigned(p,shard)
        for index in range(n):
            seed=f.seed_for(p,shard,index)
            arm=f.forced_fresh_arm(index,shard) or f.ARMS[index%len(f.ARMS)]
            obs=[f.digest(["state",seed,k])[:24] for k in range(3)]
            source_features=([f.FEATURES[index%len(f.FEATURES)]]
                             if index%3 != 0 else [])
            dense_features=set(source_features)
            raw={name:{"min":0,"max":0,"nonzero_frames":0,"transitions":0}
                 for name in f.DENSE_RAW_FIELDS}
            if "split-register-changes" in dense_features or "split-register-nonzero" in dense_features:
                dense_features.update(("split-register-changes","split-register-nonzero"))
                raw["split"].update(max=1,nonzero_frames=1,transitions=1)
            if "offscreen-register-nonzero" in dense_features:
                raw["p1_offscreen"].update(max=1,nonzero_frames=1,transitions=1)
            if "both-air-raw" in dense_features:
                for name in ("p1_air","p2_air"):
                    raw[name].update(max=1,nonzero_frames=1,transitions=1)
            dense={
                "epoch":f.DENSE_EPOCH,"frames_observed":len(f.DENSE_FRAME_NAMES),
                "features":sorted(dense_features),
                "first_frame":{
                    feature:f.DENSE_FRAME_NAMES[1] if feature in (
                        "split-register-changes","both-rotation-registers-change",
                        "checkpoint-pointer-changes") else f.DENSE_FRAME_NAMES[0]
                    for feature in dense_features},
                "raw_fields":raw,
            }
            rows.append({
                "seed":seed,"arm":arm,
                "input_sha256":f.digest(["legal-controller",seed]),
                "post_entry_wram_sha256":f.digest(["native-observed",seed]),
                "tokens":obs,
                "features": source_features,
                "dense_diagnostics":dense,
                "observation_count":len(f.guest.FRAMES)+1,
                "verified_ablation":index%25==0,
                "real_native_processes":4 if index%25==0 else 1,
                "intervals":20,"p1_intervals":17,"p2_intervals":14,
            })
            attempts[arm]+=1
            gains[arm]+=len(set(obs)-tokens)
            tokens.update(obs)
        row=f._receipt(p,shard,ident,attempts,gains,rows,tokens,
                       failure=None,started=time.monotonic(),complete=True)
        f.save(receipts/f"research-frontier-{shard}"/"result.json",row)
    return p,receipts


class ResearchFrontierContracts(unittest.TestCase):
    def test_exact_100_1000_10000_plans_cover_every_global_case_once(self):
        for cases,shards in ((100,4),(1000,10),(10000,40)):
            with self.subTest(cases=cases):
                p=f.plan(SOURCE,50000000,cases)
                f.validate_plan(p)
                self.assertEqual(p["shards"],shards)
                self.assertEqual(p["max_parallel"],4)
                generated=[f.seed_for(p,shard,i)
                           for shard in range(shards)
                           for i in range(f.assigned(p,shard)[1])]
                self.assertEqual(len(generated),cases)
                self.assertEqual(generated,list(range(50000000,50000000+cases)))
                self.assertEqual(p["release_gate_credit"],0)
                self.assertFalse(p["original_native_parity"])
        for bad in (0,11,500,9999,10001):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                f.plan(SOURCE,50000000,bad)

    def test_proven_source_prefix_is_never_mutated(self):
        for arm in f.ARMS:
            with self.subTest(arm=arm):
                a,info=f.actions_for(50000001,arm)
                self.assertEqual(a[0],(1650,60,0x080,0x040))
                self.assertGreaterEqual(info["p1_intervals"],2)
                self.assertGreaterEqual(info["p2_intervals"],2)
                self.assertTrue(all(0<=p1<=0x1ff and 0<=p2<=0x1ff
                                    for _,_,p1,p2 in a))
                self.assertGreaterEqual(len(a),8)
        seen={f.digest(f.actions_for(i,"balanced")[0]) for i in range(50000000,50000020)}
        self.assertEqual(len(seen),20)

    def test_ucb_reacts_to_novelty_and_explores_every_arm(self):
        attempted=dict.fromkeys(f.ARMS,0)
        gains=dict.fromkeys(f.ARMS,0)
        for arm in f.ARMS:
            self.assertEqual(f.select_arm(attempted,gains),arm)
            attempted[arm]+=1
        gains["rotation"]=50
        self.assertEqual(f.select_arm(attempted,gains),"rotation")
        with self.assertRaises(ValueError):
            f.select_arm({"unproven":0},gains)

    def test_fresh_exploration_is_independent_of_historical_strategy_prior(self):
        # This was the root cause of zero alternating and rotation trials in
        # the genuine 10,000-case run: every prior count was already nonzero.
        for count,shards in ((100,4),(1000,10),(10000,40)):
            per=count//shards
            all_attempts=dict.fromkeys(f.ARMS,0)
            for shard in range(shards):
                local=dict.fromkeys(f.ARMS,0)
                historical={arm:100000 for arm in f.ARMS}
                historical["balanced"]=10000000
                gains={arm:0 for arm in f.ARMS}
                gains["balanced"]=30000000
                for index in range(per):
                    required=f.forced_fresh_arm(index,shard)
                    arm=required or f.select_arm(
                        {k:historical[k]+local[k] for k in f.ARMS},gains)
                    local[arm]+=1
                    all_attempts[arm]+=1
                    if required is not None:
                        self.assertEqual(arm,required)
                self.assertTrue(all(n>=1 for n in local.values()))
                if per==250:
                    self.assertTrue(all(n>=6 for n in local.values()))
            self.assertEqual(sum(all_attempts.values()),count)
            self.assertTrue(all(all_attempts.values()))
        self.assertEqual(f.forced_fresh_arm(0,0),"balanced")
        self.assertEqual(f.forced_fresh_arm(0,1),"p1-focus")
        self.assertIsNone(f.forced_fresh_arm(5,0))
        with self.assertRaises(ValueError):
            f.forced_fresh_arm(250,0)

    def test_semantic_coverage_uses_source_fields_not_raw_wram_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            directory=Path(td)
            for name in f.FRAME_NAMES:
                (directory/(name+".wram.bin")).write_bytes(bytes(131072))
            a=f.semantic_bins(directory)
            self.assertEqual(len(a),3)
            self.assertTrue(all(len(x)==24 for x in a))
            self.assertEqual(a,f.semantic_bins(directory))
            path=directory/(f.FRAME_NAMES[0]+".wram.bin")
            blob=bytearray(path.read_bytes())
            blob[0x2000]=99
            path.write_bytes(blob)
            self.assertEqual(a,f.semantic_bins(directory))
            blob[0x411:0x413]=(320).to_bytes(2,"little")
            path.write_bytes(blob)
            self.assertNotEqual(a,f.semantic_bins(directory))

    def test_real_wram_named_source_category_features_are_distinct_from_random_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name in f.FRAME_NAMES:
                (root/(name+".wram.bin")).write_bytes(bytes(131072))
            self.assertEqual(f.source_features(root),())
            cases=[]
            for index,name in enumerate(f.FRAME_NAMES):
                path=root/(name+".wram.bin")
                data=bytearray(path.read_bytes())
                if index==1:
                    data[0x0545]=1
                    data[0x0547]=1
                    data[0x04B7:0x04B9]=(12).to_bytes(2,"little")
                    data[0x04B9:0x04BB]=(65520).to_bytes(2,"little")
                    data[0x0DDB]=1
                    data[0x121B]=1
                    data[0x1199:0x119B]=(2).to_bytes(2,"little")
                    data[0x04C7]=4
                    data[0x04C9]=8
                path.write_bytes(data)
                cases.append(data)
            categories=set(f.source_features(root))
            self.assertEqual(categories,{
                "both-air-raw","both-moving-raw",
                "both-rotation-registers-change",
                "checkpoint-pointer-changes","offscreen-register-nonzero",
                "opposing-x-motion-raw",
                "split-register-changes","split-register-nonzero",
            })
            self.assertTrue(categories.issubset(f.FEATURES))
            self.assertEqual(f.source_features(root),tuple(sorted(categories)))

    def test_dense_observer_detects_transient_raw_categories_old_three_frames_miss(self):
        with tempfile.TemporaryDirectory() as td:
            dumps=Path(td)
            for frame in f.guest.FRAMES:
                blob=bytearray(131072)
                blob[0x0DDB]=1  # split raw is nonzero across historic 3 frames
                if frame==1860:
                    blob[0x0545]=3  # both air candidates only for one intermediate frame
                    blob[0x0547]=2
                if frame==1980:
                    blob[0x121B]=5  # transient P1 offscreen
                if frame==2220:
                    blob[0x0DDB]=2  # transient split transition
                (dumps/f"endurance-{frame}.wram.bin").write_bytes(blob)
            historical=set(f.source_features(dumps))
            self.assertEqual(historical,{"split-register-nonzero"})
            diag=f.dense_source_diagnostics(dumps)
            self.assertEqual(diag["epoch"],f.DENSE_EPOCH)
            self.assertEqual(diag["frames_observed"],15)
            self.assertTrue(historical.issubset(diag["features"]))
            self.assertEqual(diag["first_frame"]["both-air-raw"],"endurance-1860")
            self.assertEqual(diag["first_frame"]["offscreen-register-nonzero"],
                             "endurance-1980")
            self.assertEqual(diag["first_frame"]["split-register-changes"],
                             "endurance-2220")
            self.assertEqual(diag["raw_fields"]["split"]["max"],2)
            self.assertEqual(diag["raw_fields"]["p1_air"]["nonzero_frames"],1)
            f.validate_dense_diagnostics({"features":list(historical),
                                          "dense_diagnostics":diag})
            fake={"features":list(historical),"dense_diagnostics":{
                **diag,"raw_fields":{**diag["raw_fields"],
                                    "split":{**diag["raw_fields"]["split"],
                                             "transitions":0}}}}
            with self.assertRaises(ValueError):
                f.validate_dense_diagnostics(fake)
            (dumps/"endurance-1980.wram.bin").unlink()
            with self.assertRaises(ValueError):
                f.dense_source_diagnostics(dumps)

    def test_one_in_25_real_process_and_seat_mutation_budget(self):
        for count,shards in ((100,4),(1000,10),(10000,40)):
            with self.subTest(count=count):
                per=count//shards
                sampled=shards*((per+24)//25)
                self.assertEqual(sampled, {100:4,1000:40,10000:400}[count])
                self.assertLessEqual(count+3*sampled,11200)
        code=(ROOT/"tools/qa_adaptive_frontier.py").read_text()
        self.assertIn("if index % 25 == 0:",code)
        self.assertIn("guest.execute(exe,rom,treatment",code)
        self.assertIn("guest.BASE_CHECK",code)
        self.assertIn("guest.FIRST_PROBE",code)

    def test_bounded_ddmin_keeps_immutable_source_entry_and_repro(self):
        actions=[(1650,60,128,64),*[(1750+i*42,10,128,0)
                                     for i in range(12)]]
        bad=actions[6]
        result=f.minimize_actions(
            actions=actions,predicate=lambda candidate: bad in candidate,
            budget=12)
        self.assertEqual(result["actions"][0],actions[0])
        self.assertIn(bad,result["actions"])
        self.assertLessEqual(result["probes"],12)
        self.assertLess(result["remaining_actions"],len(actions))
        with self.assertRaises(ValueError):
            f.minimize_actions(actions=[],predicate=lambda _:True)

    def test_four_shards_100_case_receipts_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            p,receipts=report_tree(Path(td))
            data=f.aggregate(p,receipts)
            self.assertEqual(data["disposition"],"completed_observational")
            self.assertEqual(data["completed_cases"],100)
            self.assertEqual(data["native_processes"],112)
            self.assertEqual(data["metamorphic_verified_cases"],4)
            self.assertEqual(data["observed_shards"],4)
            self.assertEqual(data["release_gate_credit"],0)
            self.assertFalse(data["original_native_parity"])
            self.assertGreater(data["semantic_bins_observed"],200)
            self.assertEqual(set(data["checkpoint_unique_fingerprints"]),set(f.FRAME_NAMES))
            self.assertTrue(all(1<=n<=100 for n in data["checkpoint_unique_fingerprints"].values()))
            self.assertGreaterEqual(sum(data["checkpoint_unique_fingerprints"].values()),
                                    data["semantic_bins_observed"])
            self.assertLessEqual(len(data["reproduction_seeds_by_fingerprint"]),256)
            # Large experiments must not hand off 256 examples all from the
            # first worker: retain distinct source-qualified arm/shard cohorts.
            covered={(v["shard"],v["arm"])
                     for v in data["reproduction_seeds_by_fingerprint"].values()}
            self.assertEqual(covered,{
                (shard,arm) for shard in range(p["shards"]) for arm in f.ARMS
            })
            self.assertEqual(sum(s["attempted"] for s in data["strategy_summary"].values()),100)
            self.assertEqual(set(data["source_feature_counts"]),set(f.FEATURES))
            self.assertGreater(sum(data["source_feature_counts"].values()),0)
            self.assertTrue(data["source_feature_reproduction_seeds"])

    def test_source_identity_wrong_count_duplicate_input_fake_credit_and_partial(self):
        for corruption in ("missing","extra","sha","wrong_source","fake_credit",
                           "partial","count","duplicate_seed","duplicate_input",
                           "forged_arm","wrong_observations","semantic_tokens",
                           "forged_forced_arm",
                           "missing_dense","forged_dense",
                           "fake_source_category","repeated_source_category"):
            with self.subTest(corruption=corruption),tempfile.TemporaryDirectory() as td:
                p,receipts=report_tree(Path(td))
                path=receipts/"research-frontier-1/result.json"
                if corruption=="missing":
                    path.unlink()
                elif corruption=="extra":
                    (receipts/"unknown-shard").mkdir()
                else:
                    row=f.read(path)
                    if corruption=="sha": row["receipt_sha256"]="0"*64
                    elif corruption=="wrong_source": row["source_sha"]="f"*40
                    elif corruption=="fake_credit": row["release_gate_credit"]=1
                    elif corruption=="partial": row["disposition"]="in_progress"
                    elif corruption=="count": row["passed_cases"]-=1
                    elif corruption=="duplicate_seed": row["case_results"][2]["seed"]=row["case_results"][1]["seed"]
                    elif corruption=="duplicate_input": row["case_results"][2]["input_sha256"]=row["case_results"][1]["input_sha256"]
                    elif corruption=="forged_arm": row["case_results"][2]["arm"]="not-a-controller-arm"
                    elif corruption=="forged_forced_arm": row["case_results"][0]["arm"]="rotation"
                    elif corruption=="missing_dense": del row["case_results"][1]["dense_diagnostics"]
                    elif corruption=="forged_dense": row["case_results"][1]["dense_diagnostics"]["epoch"]="fake"
                    elif corruption=="wrong_observations": row["case_results"][1]["observation_count"]=0
                    elif corruption=="semantic_tokens": row["semantic_bins"]=["0"*24]
                    elif corruption=="fake_source_category": row["case_results"][2]["features"]=["unknown-original-ppu"]
                    elif corruption=="repeated_source_category": row["case_results"][2]["features"]=[f.FEATURES[0],f.FEATURES[0]]
                    if corruption!="sha":
                        row["receipt_sha256"]=f.digest({
                            k:v for k,v in row.items() if k!="receipt_sha256"})
                    f.save(path,row)
                result=f.aggregate(p,receipts)
                self.assertEqual(result["disposition"],"incomplete_or_failed")
                self.assertTrue(result["issues"])
                self.assertEqual(result["release_gate_credit"],0)

    def test_manual_only_large_matrix_one_build_and_artifact_safety(self):
        wf=(ROOT/".github/workflows/qa-adaptive-frontier.yml").read_text()
        self.assertIn("workflow_dispatch:",wf)
        self.assertIn("workflow_call:",wf)
        self.assertNotIn("\n  schedule:",wf)
        self.assertNotIn("\n  pull_request:",wf)
        self.assertNotIn("\n  push:",wf)
        self.assertIn("max-parallel: 4",wf)
        self.assertIn("modern-shared-native-acceptance.yml",wf)
        self.assertIn("fromJSON(needs.plan.outputs.matrix)",wf)
        self.assertIn("timeout-minutes: 180",wf)
        self.assertIn("qa-frontier-aggregate",wf)
        self.assertNotIn(chr(92)+chr(36)+"{{",wf)
        self.assertNotIn("persist-credentials: true",wf)


if __name__=="__main__":
    unittest.main()
