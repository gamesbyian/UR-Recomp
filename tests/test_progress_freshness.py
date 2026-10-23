import unittest
from tools.check_progress_freshness import check

class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.inventory={"version":"windows-beta-v1"}
        self.log={"entries":[{"source_commit":"a"*40,"engineering_maturity_after":48.5,"changes":[{"evidence":"https://github.com/gamesbyian/UR-Recomp/pull/2392"}]}]}

    def test_exact_source_pass(self):
        self.assertEqual(check(self.inventory,self.log,"a"*40)["engineering_maturity_after"],48.5)
    def test_newer_head_refused(self):
        with self.assertRaisesRegex(ValueError,"STALE"):
            check(self.inventory,self.log,"b"*40)
    def test_missing_score_refused(self):
        self.log["entries"][-1].pop("engineering_maturity_after")
        with self.assertRaises(ValueError):
            check(self.inventory,self.log,"a"*40)
    def test_missing_evidence_refused(self):
        self.log["entries"][-1]["changes"]=[{"evidence":"unverified"}]
        with self.assertRaises(ValueError):
            check(self.inventory,self.log,"a"*40)

if __name__=="__main__":
    unittest.main()
