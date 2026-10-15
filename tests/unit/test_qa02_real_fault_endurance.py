"""Synthetic-only contracts for genuine OS-process recovery endurance."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa02_real_fault_endurance as e

SHA="a"*40
BINARY="b"*64


def fake_source_producer(**kw):
    kw["work"].mkdir(parents=True)
    row={
        "schema":e.original.SCHEMA,
        "source_sha":kw["source_sha"],
        "binary_sha256":kw["binary_sha256"],
        "suite":kw["suite"],"seed":kw["seed"],
        "requested_iterations":kw["iterations"],
        "attempted_iterations":kw["iterations"],
        "passed_iterations":kw["iterations"],
        "failed_iterations":0,"disposition":"completed_positive",
        "failures":[],"elapsed_ms":234,
        "retained_failure_root_count":0,"release_gate_credit":0,
        "physical_hardware_covered":False,
        "actual_guest_gameplay_covered":False,
    }
    row["receipt_sha256"]=e.original.json_hash(row)
    return row


def fake_one(root:Path,suite:str,max_chunks:int=2):
    path=root/("fault-endurance-"+suite)/"result.json"
    with mock.patch.object(e.original,"digest",return_value=BINARY),\
         mock.patch.object(e.original,"run_suite",side_effect=fake_source_producer):
        # avoid compiled fixtures in dependency-free unit test
        fixture=root/"fixture"
        fixture.touch()
        return e.run_shard(
            exe=fixture,source_sha=SHA,binary_sha=BINARY,
            suite=suite,minutes=15,seed=20261011,
            work=root/("work-"+suite),
            result_path=path,max_chunks=max_chunks)


def populate(root:Path,max_chunks:int=2):
    recs=root/"receipts"
    recs.mkdir()
    for suite in e.SUITES:
        report=fake_one(root,suite,max_chunks)
        e.save(recs/("fault-endurance-"+suite)/"result.json",report)
    return recs


class FaultEnduranceContracts(unittest.TestCase):
    def test_five_live_original_production_scenarios_and_bounded_hours(self):
        self.assertEqual(e.SUITES,("c09-orphan","c14-c15-receipt","qa03-midseries",
                                   "hardkill-owner","c16-storage-outage"))
        self.assertEqual(e.MINUTES,(15,60,120))
        self.assertEqual(e.CHUNK_SIZE,10)
        self.assertEqual(e.MAX_CHUNKS,20000)
        for suite in e.SUITES:
            self.assertTrue(callable(e.original.IMPLEMENTATIONS[suite]))

    def test_new_timing_seeds_and_source_producer_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with mock.patch.object(e.original,"digest",return_value=BINARY),\
                 mock.patch.object(e.original,"run_suite",side_effect=fake_source_producer) as producer:
                fixture=root/"fixture"
                fixture.touch()
                row=e.run_shard(
                    exe=fixture,source_sha=SHA,binary_sha=BINARY,
                    suite="hardkill-owner",minutes=15,seed=20261011,
                    work=root/"work",result_path=root/"result.json",max_chunks=3)
            self.assertEqual(producer.call_count,3)
            self.assertEqual(row["disposition"],"completed_positive")
            self.assertEqual(row["stop_reason"],"case_cap")
            self.assertEqual(row["observed_complete_chunks"],3)
            self.assertEqual(row["real_process_fault_journeys"],30)
            self.assertEqual(sum(row["timing_jitter_ms_histogram"]),30)
            self.assertEqual(len(set(c["seed"] for c in row["chunks"])),3)
            for index,chunk in enumerate(row["chunks"]):
                self.assertEqual(chunk["index"],index)
                self.assertEqual(chunk["seed"],e.case_seed(20261011,"hardkill-owner",index))
                self.assertEqual(sum(chunk["jitter_ms_histogram"]),10)
            self.assertFalse(row["power_loss_equivalence_claimed"])
            self.assertFalse(row["actual_guest_gameplay_covered"])
            self.assertFalse(row["physical_hardware_covered"])
            self.assertEqual(row["release_gate_credit"],0)

    def test_five_distinct_receipts_aggregate_and_real_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            receipts=populate(root)
            report=e.aggregate(receipts,SHA,BINARY,15,20261011,max_chunks=2)
            self.assertEqual(report["disposition"],"completed_positive")
            self.assertEqual(report["observed_suites"],5)
            self.assertEqual(report["completed_unique_timing_batches"],10)
            self.assertEqual(report["completed_real_fault_process_journeys"],100)
            self.assertEqual(report["release_gate_credit"],0)
            self.assertNotIn("release_accepted",json.dumps(report))

    def test_fail_closed_on_missing_partial_false_credit_wrong_seeds_and_identity(self):
        for fault in ("missing","extra","receipt","credit","binary","seed","count",
                      "jitter","chunk-digest","partial","claimed-hardware","duplicate","reason"):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                receipts=populate(root)
                target=receipts/"fault-endurance-c16-storage-outage/result.json"
                if fault=="missing":
                    target.unlink()
                elif fault=="extra":
                    (receipts/"fault-endurance-unknown").mkdir()
                else:
                    report=json.loads(target.read_text())
                    if fault=="receipt":report["receipt_sha256"]="0"*64
                    elif fault=="credit":report["release_gate_credit"]=1
                    elif fault=="binary":report["binary_sha256"]="c"*64
                    elif fault=="seed":report["chunks"][1]["seed"]+=1
                    elif fault=="count":report["real_process_fault_journeys"]=200
                    elif fault=="jitter":report["timing_jitter_ms_histogram"]=[0]*9
                    elif fault=="chunk-digest":report["chunks"][0]["source_receipt_sha256"]="?"
                    elif fault=="partial":report["disposition"]="in_progress"
                    elif fault=="claimed-hardware":report["physical_hardware_covered"]=True
                    elif fault=="duplicate":report["chunks"][1]["index"]=0
                    elif fault=="reason":report["stop_reason"]="runtime_padded"
                    if fault!="receipt":
                        report["receipt_sha256"]=e.digest_object({
                            k:v for k,v in report.items() if k!="receipt_sha256"})
                    e.save(target,report)
                agg=e.aggregate(receipts,SHA,BINARY,15,20261011,max_chunks=2)
                self.assertEqual(agg["disposition"],"incomplete_or_failed")
                self.assertTrue(agg["issues"])
                self.assertEqual(agg["release_gate_credit"],0)

    def test_original_trial_failure_never_promoted_and_partial_report_kept(self):
        def broken(**kw):
            row=fake_source_producer(**kw)
            row["passed_iterations"]=9
            row["failed_iterations"]=1
            row["failures"]=[{"trial":9,"kind":"TrialError","error":"owner conflict"}]
            unsigned={k:v for k,v in row.items() if k!="receipt_sha256"}
            row["receipt_sha256"]=e.original.json_hash(unsigned)
            return row
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            fixture=root/"fixture"
            fixture.touch()
            dest=root/"receipt.json"
            with mock.patch.object(e.original,"digest",return_value=BINARY),\
                 mock.patch.object(e.original,"run_suite",side_effect=broken):
                row=e.run_shard(
                    exe=fixture,source_sha=SHA,binary_sha=BINARY,
                    suite="hardkill-owner",minutes=15,seed=20261011,
                    work=root/"private",result_path=dest,max_chunks=2)
            self.assertEqual(row["disposition"],"invariant_violation")
            self.assertEqual(row["real_process_fault_journeys"],0)
            self.assertEqual(len(row["failed_chunks"]),1)
            self.assertEqual(json.loads(dest.read_text())["disposition"],"invariant_violation")
            self.assertTrue((root/"private/batch-00000").exists())

    def test_workflow_manual_only_single_build_bounded_runner_and_partial_evidence(self):
        wf=(ROOT/".github/workflows/qa02-real-fault-endurance.yml").read_text()
        self.assertIn("workflow_dispatch:",wf)
        self.assertNotIn("\n  pull_request:",wf)
        self.assertNotIn("\n  push:",wf)
        self.assertNotIn("schedule:",wf)
        self.assertIn("max-parallel: ${{ fromJSON(inputs.max_parallel || '3') }}", wf)
        self.assertIn('options: ["1", "3", "5"]', wf)
        self.assertEqual(wf.count("      max_parallel:"), 2)
        self.assertEqual(wf.count('default: "3"'), 2)
        self.assertIn("suite: [c09-orphan, c14-c15-receipt, qa03-midseries, hardkill-owner, c16-storage-outage]", wf)
        self.assertIn("timeout-minutes: 145",wf)
        self.assertIn('options: ["15", "60", "120"]',wf)
        self.assertIn("qa02_recovery_campaign.py build",wf)
        self.assertNotIn("cmake --build",wf)
        self.assertIn("continue-on-error: true",wf)
        self.assertIn("if: always()",wf)
        self.assertIn("qa02-real-fault-endurance-aggregate",wf)
        self.assertNotIn(chr(92)+chr(36)+"{{",wf)
        for suite in e.SUITES:self.assertIn(suite,wf)
        code=(ROOT/"tools/qa02_real_fault_endurance.py").read_text()
        self.assertIn("original.run_suite(",code)
        self.assertIn("original.json_hash(data)",code)
        self.assertNotIn("def suite_hardkill",code)
        self.assertNotIn("def suite_outage",code)


if __name__=="__main__":
    unittest.main()
