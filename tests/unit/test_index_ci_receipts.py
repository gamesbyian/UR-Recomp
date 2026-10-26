"""Offline evidence indexing never exports raw receipts or releases gate credit."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from tools import index_ci_receipts as m

SHA = "a"*40

def unit(outcome="pass"):
    return {"schema": "UR-CI-UNIT-RESULT/1", "authority": "diagnostic-only",
            "source": {"GITHUB_SHA": SHA}, "outcome": outcome,
            "total_tests_observed": 10,
            "shards": [{"outcome": outcome}],
            "missing_evidence": []}

def windows(ok=True):
    return {"schema": "ur-win32-acceptance-fanout-aggregate/2",
            "source_sha": SHA, "expected_cases": 13,
            "observed_cases": 13 if ok else 12,
            "transport_complete": ok, "issues": [] if ok else ["missing group"],
            "failed_cases": [], "release_gate_credit": 0,
            "independent_physical_qa": False}

class IndexTests(unittest.TestCase):
    def test_two_receipts_idempotent_privacy_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            paths=[]
            for i,value in enumerate((unit(),windows())):
                p=root/f"private-{i}.json"
                value["private_user_token"]="DO_NOT_PUBLISH"
                p.write_text(json.dumps(value))
                paths.append(p)
            db=root/"index.sqlite3"
            m.ingest(db,paths)
            m.ingest(db,paths)
            rows=m.query(db,SHA,25)
            self.assertEqual(len(rows),2)
            self.assertTrue(all(x["release_gate_credit"]==0 for x in rows))
            self.assertNotIn("DO_NOT_PUBLISH",db.read_bytes().decode("latin-1"))
            self.assertNotIn("private-",db.read_bytes().decode("latin-1"))
            self.assertTrue(all(len(row["digest"])==64 for row in rows))

    def test_invalid_second_receipt_rolls_back_entire_batch(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            ok=root/"good.json"
            bad=root/"bad.json"
            ok.write_text(json.dumps(unit()))
            bad.write_text(json.dumps({"schema":"unknown"}))
            with self.assertRaises(ValueError):
                m.ingest(root/"db.sqlite", [ok,bad])
            self.assertFalse((root/"db.sqlite").exists())

    def test_claimed_release_credit_and_false_success_rejected(self):
        for x in ({**windows(), "release_gate_credit":1},
                  {**windows(), "observed_cases":12},
                  {**windows(), "independent_physical_qa":True},
                  {**unit(), "missing_evidence":["shard1"]},
                  {**unit(), "shards":[{"outcome":"fail"}]}):
            with self.subTest(x=x):
                with self.assertRaises(ValueError):
                    m.project(x)

    def test_incomplete_case_and_failing_unit_preserved(self):
        w=m.project(windows(False))
        self.assertEqual((w["outcome"],w["missing"] ),("incomplete",1))
        f=m.project(unit("fail"))
        self.assertEqual((f["outcome"],f["failures"]),("fail",1))

    def test_query_source_bound_and_bounds(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            p=root/"unit.json"
            p.write_text(json.dumps(unit()))
            db=root/"db.sqlite"
            m.ingest(db,[p])
            self.assertEqual(m.query(db,"b"*40,25),[])
            with self.assertRaises(ValueError):
                m.query(db,SHA,101)

if __name__=="__main__":
    unittest.main()
