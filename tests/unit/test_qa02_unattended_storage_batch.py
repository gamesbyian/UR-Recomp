"""Read-only parent transport tests for two existing QA-02 stress campaigns."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tools"))
import qa02_unattended_storage_batch as parent

SOURCE="a"*40
BINARY="b"*64

def fixtures(root: Path, count: int=10) -> tuple[Path, Path]:
    c12=root/"c12.json"
    recovery=root/"recovery.json"
    c12.write_text(json.dumps({
        "schema":"ur-qa02-c12-campaign-aggregate/1", "source_commit":SOURCE,
        "binary_sha256":BINARY, "requested_trials":count*4,
        "observed_trials":count*4, "passed_trials":count*4,
        "failed_trials":0, "missing_shards":[], "invalid_shards":[],
        "failing_shards":[], "disposition":"completed_positive",
        "release_gate_credit":0,
    }))
    recovery.write_text(json.dumps({
        "schema":"ur-qa02-recovery-campaign/1", "source_sha":SOURCE,
        "binary_sha256":"c"*64, "requested_suite_count":5,
        "completed_suite_count":5, "requested_iterations":count*5,
        "observed_iterations":count*5, "passed_iterations":count*5,
        "failed_iterations":0, "issues":[],
        "disposition":"completed_positive", "release_gate_credit":0,
        "physical_hardware_covered":False,"actual_guest_gameplay_covered":False,
        "suites":[{"suite":k} for k in (
            "c09-orphan","c14-c15-receipt","qa03-midseries",
            "hardkill-owner","c16-storage-outage")],
    }))
    return c12,recovery


class StorageSupercampaignTests(unittest.TestCase):
    def test_success_requires_both_original_receipts_and_all_nine_shards(self):
        with tempfile.TemporaryDirectory() as td:
            c12,recovery=fixtures(Path(td))
            report=parent.make_result(SOURCE,"381",10,"success","success",c12,recovery)
            self.assertEqual(report["disposition"],"completed_positive")
            self.assertEqual(report["total_expected_real_process_trials"],90)
            self.assertEqual(report["verified_successful_real_process_trials"],90)
            self.assertEqual(report["release_gate_credit"],0)
            self.assertFalse(report["authentic_guest_2p_match_played"])
            self.assertFalse(report["physical_hardware_witness"])
            self.assertFalse(report["complete_original_native_event_equality"])
            self.assertEqual(set(report["underlying_binary_sha256"]),{"c12","recovery"})

    def test_fail_closed_on_child_job_failure_missingness_and_forgery(self):
        for kind in ("missing_c12","missing_recovery","c12_failure","recovery_cancelled",
                     "wrong_sha","false_c12_count","false_recovery_pass",
                     "false_credit","hardware_claim","incomplete_cohort"):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
                c12,recovery=fixtures(Path(td))
                status=("success","success")
                if kind=="missing_c12":c12.unlink()
                elif kind=="missing_recovery":recovery.unlink()
                elif kind=="c12_failure":status=("failure","success")
                elif kind=="recovery_cancelled":status=("success","cancelled")
                else:
                    file = c12 if kind in ("wrong_sha","false_c12_count","false_credit") else recovery
                    row=json.loads(file.read_text())
                    if kind=="wrong_sha":row["source_commit"]="f"*40
                    elif kind=="false_c12_count":row["passed_trials"]=39
                    elif kind=="false_recovery_pass":row["passed_iterations"]=49
                    elif kind=="false_credit":row["release_gate_credit"]=1
                    elif kind=="hardware_claim":row["physical_hardware_covered"]=True
                    elif kind=="incomplete_cohort":row["suites"]=row["suites"][:-1]
                    file.write_text(json.dumps(row))
                report=parent.make_result(SOURCE,"382",10,*status,c12,recovery)
                self.assertEqual(report["disposition"],"incomplete_or_failed")
                self.assertTrue(report["issues"])
                self.assertEqual(report["release_gate_credit"],0)

    def test_wrong_expected_population_and_bad_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            c12,recovery=fixtures(Path(td))
            for size in (0,1,9,501):
                with self.subTest(size=size),self.assertRaises(ValueError):
                    parent.make_result(SOURCE,"33",size,"success","success",c12,recovery)
            with self.assertRaises(ValueError):
                parent.make_result("bad","33",10,"success","success",c12,recovery)

    def test_workflows_reuse_existing_producers_and_are_manually_triggered(self):
        main=(ROOT/".github/workflows/qa02-unattended-storage-batch.yml").read_text()
        self.assertIn("workflow_dispatch:", main)
        self.assertNotIn("\n  pull_request:",main)
        self.assertNotIn("\n  push:",main)
        self.assertNotIn("schedule:",main)
        self.assertIn("cancel-in-progress: false",main)
        self.assertIn("qa02-c12-process-race-campaign.yml",main)
        self.assertIn("qa02-recovery-cohort.yml",main)
        self.assertIn("qa02_unattended_storage_batch.py",main)
        self.assertIn("name: qa02-c12-campaign-aggregate",main)
        self.assertIn("name: qa02-recovery-aggregate",main)
        self.assertNotIn(chr(92)+chr(36)+"{{",main)
        for path in ("qa02-c12-process-race-campaign.yml","qa02-recovery-cohort.yml"):
            called=(ROOT/".github/workflows"/path).read_text()
            self.assertIn("workflow_call:",called)
            self.assertIn("workflow_dispatch:",called)
            self.assertNotIn(chr(92)+chr(36)+"{{",called)
        # Distinct original build fixtures are intentional; no third build.
        self.assertNotIn("cmake --build",main)
        self.assertNotIn("g++ ",main)


if __name__=="__main__":
    unittest.main()
