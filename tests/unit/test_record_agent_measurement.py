"""One-command agent measurement authoring is validated and append-only."""
import argparse
import json
import tempfile
import unittest
from pathlib import Path

from tools.daily_measurement import validate_milestones, job_ranges, load
from tools.record_agent_measurement import make_entry

ROOT=Path(__file__).resolve().parents[2]

class EntryAuthoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.i=load(ROOT/"docs/progress/windows-beta-v2-inventory.json")
        cls.p=load(ROOT/"docs/progress/remaining-work-prior-v1.json")
        cls.a=load(ROOT/"docs/progress/remaining-work-adjustments.json")
        cls.m=validate_milestones(load(ROOT/"docs/progress/daily/milestones-v1.json"),cls.i)
        cls.jobs=job_ranges(cls.p,cls.i,cls.a)
    def args(self,**changes):
        kw=dict(id="qualified-wheel-ring-test", kind="milestone", work_id="UR-ART-4K",
          source_sha=self.i["source_sha"], pr="https://github.com/gamesbyian/UR-Recomp/pull/3101",
          actor="producer", outcome="Verified exact five-parent GLB after independent source registration",
          remaining="Original animated final art and owner review remain unavailable",
          evidence=["https://github.com/gamesbyian/UR-Recomp/pull/3101"],
          milestone="ART-05-PIVOTS",state=None,reviewer=None,job_id=None,from_range=None,
          to=None,reason_type="re_estimate",reason=None,when="2026-11-06T23:00:00Z")
        kw.update(changes)
        return argparse.Namespace(**kw)
    def test_default_provisional_with_real_milestone(self):
        e=make_entry(self.args(),self.m,self.jobs)
        self.assertEqual(e["milestone_state"],"provisional")
        self.assertEqual(e["milestone_id"],"ART-05-PIVOTS")
        self.assertNotIn("effort_update",e)
    def test_research_cannot_earn_milestone_credit(self):
        with self.assertRaisesRegex(ValueError,"Only milestone"):
            make_entry(self.args(kind="research"),self.m,self.jobs)
        e=make_entry(self.args(kind="research",milestone=None),self.m,self.jobs)
        self.assertNotIn("milestone_id",e)
    def test_review_requires_separate_identity(self):
        with self.assertRaisesRegex(ValueError,"different"):
            make_entry(self.args(state="reviewed"),self.m,self.jobs)
        with self.assertRaisesRegex(ValueError,"distinct reviewer"):
            make_entry(self.args(state="reviewed",reviewer="producer"),self.m,self.jobs)
        e=make_entry(self.args(state="reviewed",reviewer="real-other-reviewer"),self.m,self.jobs)
        self.assertEqual(e["reviewed_by"],"real-other-reviewer")
    def test_source_and_stale_effort_checks(self):
        with self.assertRaisesRegex(ValueError,"exact 40-character"):
            make_entry(self.args(source_sha="bad"),self.m,self.jobs)
        with self.assertRaisesRegex(ValueError,"--to requires"):
            make_entry(self.args(to=[5,17,50]),self.m,self.jobs)
        e=make_entry(self.args(job_id="ART-05",from_range=[6,20,70],
                to=[5,18,61],reason="Actually eliminated an authored animation partial task"),
            self.m,self.jobs)
        self.assertEqual(e["effort_update"]["to"],[5.0,18.0,61.0])
    def test_milestone_registry_expansion_is_still_frozen_weight(self):
        parents={}
        for m in self.m.values():
            parents[m["criterion_id"]]=parents.get(m["criterion_id"],0)+m["weight_units"]
        self.assertEqual(parents["ART-04"],45)
        self.assertEqual(parents["ONE-09"],45)
        self.assertEqual(parents["QA-04"],45)
        self.assertEqual(parents["FID-01"],10)
        self.assertEqual(len(self.m),50)

if __name__=="__main__":
    unittest.main()
