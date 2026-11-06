"""Daily snapshots must preserve source, freeze methodology and reject fake velocity."""
import copy
import tempfile
import unittest
from pathlib import Path
from tools.daily_estimate_snapshot import (make_snapshot, compare, save_once, canonical_hash)
from tools.daily_measurement import load

ROOT=Path(__file__).resolve().parents[2]

class DailySnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.i=load(ROOT/"docs/progress/windows-beta-v2-inventory.json")
        cls.l=load(ROOT/"docs/RELEASE-QUALITY-LEDGER.json")
        cls.p=load(ROOT/"docs/progress/remaining-work-prior-v1.json")
        cls.a=load(ROOT/"docs/progress/remaining-work-adjustments.json")
        cls.m=load(ROOT/"docs/progress/daily/milestones-v1.json")
        cls.sha=cls.i["source_sha"]

    def snapshot(self,day,entries=(),milestones=None,adjustments=None):
        return make_snapshot(self.i,self.l,self.p,
            adjustments or self.a,milestones or self.m,list(entries),
            self.sha,day,"0"*64)

    def test_snapshot_is_source_bound_and_separates_formal_gate(self):
        a=self.snapshot("2026-11-06")
        self.assertEqual(a["engineering_estimate_percent"],56.0)
        self.assertEqual(a["remaining_relative_work_units"],895.6)
        self.assertEqual(a["formal_bounded_percent"],56.0)
        self.assertEqual(a["usa_events_accepted"],0)
        self.assertEqual(a["release_gates_passed"],0)
        self.assertEqual(a["source_main_sha"],self.sha)

    def test_same_method_makes_comparable_deltas(self):
        a=self.snapshot("2026-11-05")
        b=self.snapshot("2026-11-06")
        t=compare(a,b)
        self.assertTrue(t["comparable"])
        self.assertEqual(t["engineering_change_pp"],0)
        self.assertEqual(t["remaining_work_change_units"],0)
        self.assertEqual(t["new_event_ids"],[])

    def test_pending_source_earned_milestone_makes_real_delta(self):
        a=self.snapshot("2026-11-05")
        event=dict(schema="ur-agent-work-measurement/1",
                   event_id="test-source-receipt-stable",
                   recorded_at="2026-11-06T02:00:00Z",
                   source_main_sha=self.sha,
                   source_pr="https://github.com/gamesbyian/UR-Recomp/pull/3101",
                   kind="milestone",work_id="UR-ART-4K",
                   recorded_by="test-producer",milestone_id="ART-05-PIVOTS",
                   milestone_state="provisional",outcome="Actual source GLB parent transforms verified",
                   remaining="No native original-accurate animation or final approval",
                   evidence=["https://github.com/gamesbyian/UR-Recomp/pull/3101"])
        b=self.snapshot("2026-11-06",[event])
        t=compare(a,b)
        self.assertTrue(t["comparable"])
        self.assertEqual(t["new_event_ids"],["test-source-receipt-stable"])
        self.assertEqual(t["engineering_change_pp"],0.1)
        self.assertEqual(t["remaining_work_change_units"],0)
        self.assertEqual(t["formal_acceptance_change_pp"],0)

    def test_method_changes_cannot_fake_progress(self):
        a=self.snapshot("2026-11-05")
        modified=copy.deepcopy(self.m)
        modified["milestones"].append(dict(
            id="WIDE-08-STABLE-NEW",criterion_id="WIDE-08",weight_units=9,
            deliverable="Known real split-screen reference sequence",
            limitation="Not final accepted physical viewport"))
        b=self.snapshot("2026-11-06",milestones=modified)
        t=compare(a,b)
        self.assertFalse(t["comparable"])
        self.assertIn("milestone_allocation_sha256",t["incompatible_fields"])
        self.assertIsNone(t["engineering_change_pp"])

    def test_metadata_only_prior_update_does_not_rebaseline(self):
        a=self.snapshot("2026-11-05")
        upd=copy.deepcopy(self.a)
        upd["as_of_main_sha"]="f"*40
        upd["review_scope"]="The metadata changed but no task assumptions did"
        b=self.snapshot("2026-11-06",adjustments=upd)
        self.assertTrue(compare(a,b)["comparable"])

    def test_removed_events_and_inverted_dates_fail_closed(self):
        a=self.snapshot("2026-11-05")
        b=self.snapshot("2026-11-06")
        a["evidence_event_ids"]=["previous-receipt"]
        with self.assertRaisesRegex(ValueError,"removed"):
            compare(a,b)
        with self.assertRaisesRegex(ValueError,"earlier UTC"):
            compare(b,a)
        with self.assertRaisesRegex(ValueError,"calendar day"):
            self.snapshot("2026-02-30")

    def test_immutable_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"snapshots"/"2026-11-06.json"
            save_once(path,{"schema":"ur-daily-estimate-snapshot/1","test":7})
            with self.assertRaisesRegex(ValueError,"Refusing to overwrite"):
                save_once(path,{"test":8})
            self.assertEqual(load(path)["test"],7)

if __name__=="__main__":
    unittest.main()
