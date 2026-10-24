import copy
import json
import unittest
from pathlib import Path
from tools.progress_report import build_report

ROOT=Path(__file__).resolve().parents[1]

class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory=json.loads((ROOT/"docs/PROGRESS-INVENTORY.json").read_text())
        cls.ledger=json.loads((ROOT/"docs/RELEASE-QUALITY-LEDGER.json").read_text())
        cls.log=json.loads((ROOT/"docs/PROGRESS-CHANGELOG.json").read_text())

    def test_latest_interval(self):
        last=self.log["entries"][-1]
        report=build_report(self.inventory,self.ledger,self.log,last["source_commit"])
        self.assertEqual(report["engineering_maturity_percent"],48.5)
        self.assertEqual(report["engineering_maturity_delta_points"],0)
        self.assertEqual(report["new_unique_evidence_items"],10)

    def test_stale_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"STALE"):
            build_report(self.inventory,self.ledger,self.log,"b"*40)

    def test_duplicate_receipt_rejected(self):
        data=copy.deepcopy(self.log)
        data["entries"][-1]["changes"].append(copy.deepcopy(data["entries"][-1]["changes"][0]))
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            build_report(self.inventory,self.ledger,data,data["entries"][-1]["source_commit"])

    def test_unsupported_score_override_rejected(self):
        data=copy.deepcopy(self.log)
        data["entries"][-1]["engineering_maturity_after"]=99
        with self.assertRaisesRegex(ValueError,"differs"):
            build_report(self.inventory,self.ledger,data,data["entries"][-1]["source_commit"])

if __name__=="__main__":
    unittest.main()
