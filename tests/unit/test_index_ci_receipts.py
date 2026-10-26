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


    def test_PR_synthetic_merge_is_not_falsely_indexed_under_PR_head(self):
        pr_head = "b" * 40
        event_sha = "c" * 40
        actual_checkout = "d" * 40
        data = unit()
        data["source"] = {
            "pr_head_sha": pr_head,
            "GITHUB_SHA": event_sha,
            "checked_out_sha": actual_checkout,
        }
        projected = m.project(data)
        self.assertEqual(projected["source_sha"], actual_checkout)
        self.assertEqual(projected["source_binding"],
                         "git_checkout_head_at_receipt")
        self.assertEqual(projected["pr_head_sha"], pr_head)
        self.assertEqual(projected["actions_event_sha"], event_sha)
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "unit.json"
            p.write_text(json.dumps(data))
            db = Path(temp) / "index.sqlite"
            m.ingest(db, [p])
            self.assertEqual(m.query(db, pr_head, 10), [])
            self.assertEqual(m.query(db, event_sha, 10), [])
            indexed = m.query(db, actual_checkout, 10)
            self.assertEqual(len(indexed), 1)
            self.assertEqual(indexed[0]["source_binding"],
                             "git_checkout_head_at_receipt")

    def test_older_receipt_only_environment_SHA_is_not_qualified_checkout(self):
        data = unit()
        data["source"] = {"GITHUB_SHA": "c" * 40, "pr_head_sha": "b" * 40}
        result = m.project(data)
        self.assertEqual(result["source_sha"], "c" * 40)
        self.assertEqual(result["source_binding"],
                         "actions_event_sha_checkout_unverified")
        self.assertNotEqual(result["source_sha"], data["source"]["pr_head_sha"])

    def test_legacy_database_must_be_preserved_and_rebuilt_not_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "legacy.sqlite"
            with sqlite3.connect(db) as con:
                con.executescript(m.DDL)
                con.execute("PRAGMA user_version=0")
            p = Path(temp) / "unit.json"
            p.write_text(json.dumps(unit()))
            with self.assertRaisesRegex(ValueError, "legacy CI receipt"):
                m.ingest(db, [p])
            with self.assertRaisesRegex(ValueError, "legacy CI receipt"):
                m.query(db, SHA, 10)
            self.assertTrue(db.is_file())
            fresh = Path(temp) / "rebuilt-v2.sqlite"
            m.ingest(fresh, [p])
            self.assertEqual(len(m.query(fresh, SHA, 10)), 1)

    def test_conflicting_or_malformed_unit_source_fields_fail_closed(self):
        for invalid in (
            {"GITHUB_SHA": SHA, "checked_out_sha": "oops"},
            {"GITHUB_SHA": "invalid", "pr_head_sha": SHA},
            {"pr_head_sha": SHA},
        ):
            data = unit()
            data["source"] = invalid
            with self.subTest(source=invalid):
                with self.assertRaisesRegex(ValueError, "SHA|source|checked_out_sha"):
                    m.project(data)

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
