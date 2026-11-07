"""Offline daily task measurement invariants. No GitHub API, ROM or CI needed."""
import copy
import json
import unittest
from pathlib import Path

from tools.daily_measurement import calculate_daily, validate_milestones, job_ranges

ROOT = Path(__file__).resolve().parents[2]

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

class DailyMeasurementsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.i = read("docs/progress/windows-beta-v2-inventory.json")
        cls.l = read("docs/RELEASE-QUALITY-LEDGER.json")
        cls.p = read("docs/progress/remaining-work-prior-v1.json")
        cls.a = read("docs/progress/remaining-work-adjustments.json")
        cls.m = read("docs/progress/daily/milestones-v1.json")
        cls.sha = cls.i["source_sha"]

    def event(self, mid="ART-05-PIVOTS", state="provisional"):
        return dict(schema="ur-agent-work-measurement/1",
                    event_id="art-five-part-pivot-a",
                    recorded_at="2026-11-06T21:30:00Z",
                    source_main_sha=self.sha,
                    source_pr="https://github.com/gamesbyian/UR-Recomp/pull/3101",
                    kind="milestone", work_id="UR-ART-4K",
                    recorded_by="implementation-agent", milestone_id=mid,
                    milestone_state=state,
                    outcome="Experimental five-parent source-bound rig passes mechanical joint test",
                    remaining="Owner likeness, full source motion and production runtime are unaccepted",
                    evidence=["https://github.com/gamesbyian/UR-Recomp/pull/3101"])

    def calc(self, events, milestones=None):
        return calculate_daily(self.i,self.l,self.p,self.a,
                               milestones or self.m,events,self.sha,self.sha)

    def test_methodology_hash_changes_when_milestone_allocation_changes(self):
        from copy import deepcopy
        original=self.calc([])
        modified=deepcopy(self.m)
        # Add a distinct *pending* criterion without changing prior milestone credits.
        modified["milestones"].append({
            "id":"WIDE-08-BASELINE-CAMERA",
            "criterion_id":"WIDE-08",
            "weight_units":9,
            "deliverable":"Pinned actual two-player split-screen moving camera evidence",
            "limitation":"A split-screen baseline alone does not qualify the shipping viewport.",
        })
        after=self.calc([],modified)
        self.assertEqual(after["engineering_estimate_percent"],original["engineering_estimate_percent"])
        self.assertNotEqual(after["model"],original["model"])
        self.assertNotEqual(after["milestone_allocation_sha256"],original["milestone_allocation_sha256"])

    def test_baseline_tracks_existing_forecast_without_double_count(self):
        result=self.calc([])
        self.assertEqual(result["engineering_estimate_percent"],56.0)
        self.assertEqual(result["relative_work_units"],895.6)
        self.assertEqual(result["usa_events_accepted"],0)
        self.assertEqual(result["release_gates_passed"],0)

    def test_provisional_milestone_has_explicit_uncertainty_not_formal_credit(self):
        result=self.calc([self.event()])
        self.assertEqual(result["engineering_estimate_percent"],56.1)
        self.assertEqual(result["engineering_recorded_evidence_range_percent"],[56.0,56.2])
        self.assertEqual(result["formal_bounded_percent"],56.0)
        self.assertEqual(result["relative_work_units"],895.6)

    def test_independent_review_and_duplicate_ids(self):
        e=self.event(state="reviewed")
        with self.assertRaisesRegex(ValueError,"distinct reviewer"):
            self.calc([e])
        e["reviewed_by"]="independent-reviewer"
        self.assertEqual(self.calc([e])["engineering_estimate_percent"],56.2)
        with self.assertRaisesRegex(ValueError,"Duplicate event ID"):
            self.calc([e,e])

    def test_last_milestone_state_replaces_prior_not_adds_it(self):
        a=self.event()
        b=self.event(state="reviewed")
        b.update(event_id="art-five-part-pivot-b",recorded_at="2026-11-06T22:00:00Z",
                 reviewed_by="different-person")
        c=self.event(state="withdrawn")
        c.update(event_id="art-five-part-pivot-c",recorded_at="2026-11-06T22:20:00Z")
        self.assertEqual(self.calc([a,b])["engineering_estimate_percent"],56.2)
        self.assertEqual(self.calc([a,b,c])["engineering_estimate_percent"],56.0)

    def test_effort_revision_is_prospective_not_double_counted(self):
        e=self.event()
        e["kind"]="effort_revision"
        e.pop("milestone_id")
        e.pop("milestone_state")
        e["effort_update"]=dict(job_id="ART-02", **{
            "from":[6,20,70], "to":[5,18,60],
            "reason_type":"earned",
            "reason":"Source-tested partial model reduces expected remaining authored rig work",
        })
        result=self.calc([e])
        self.assertEqual(result["engineering_estimate_percent"],56.0)
        self.assertAlmostEqual(result["relative_work_units"],891.2,places=1)
        self.assertEqual(result["work_unit_delta_from_recorded_revisions"],-4.3)
        nxt=copy.deepcopy(e)
        nxt.update(event_id="art-effort-revision-b",recorded_at="2026-11-06T22:00:00Z")
        with self.assertRaisesRegex(ValueError,"Stale or duplicate"):
            self.calc([e,nxt])
        e["effort_update"]["job_id"]="ONE-03"
        with self.assertRaisesRegex(ValueError,"active, uncompleted"):
            self.calc([e])

    def test_nonplayer_research_and_ci_never_earn_product_credit(self):
        e=self.event()
        e["kind"]="infrastructure"
        e.pop("milestone_id")
        e.pop("milestone_state")
        self.assertEqual(self.calc([e])["engineering_estimate_percent"],56.0)
        e["milestone_id"]="ART-02-SCOPED-SOURCE"
        with self.assertRaisesRegex(ValueError,"Only milestone"):
            self.calc([e])

    def test_fid_partial_never_promotes_formal_event(self):
        e=self.event(mid="FID-01-FIRST-CAUSE",state="reviewed")
        e["reviewed_by"]="reviewer"
        z=self.calc([e])
        self.assertEqual(z["usa_events_accepted"],0)
        self.assertEqual(z["release_gates_passed"],0)
        self.assertGreater(z["engineering_estimate_percent"],56.0)

    def test_weights_and_contract_are_frozen(self):
        over=copy.deepcopy(self.m)
        over["milestones"].append(dict(id="ART-02-EXCESS",
            criterion_id="ART-02",weight_units=1,
            deliverable="An extra overlapping stage",limitation="Not separate"))
        with self.assertRaisesRegex(ValueError,"exceed frozen parent"):
            validate_milestones(over,self.i)
        over=copy.deepcopy(self.m)
        over["contract"]="00000000"
        with self.assertRaisesRegex(ValueError,"fingerprint"):
            validate_milestones(over,self.i)

if __name__=="__main__":
    unittest.main()
