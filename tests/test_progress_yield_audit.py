import copy
import json
import unittest
from pathlib import Path
from tools.progress_yield_audit import summarize

ROOT=Path(__file__).resolve().parents[1]
class YieldAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/"docs/progress/merge-outcome-audit-20261024.json").read_text(encoding="utf-8"))
    def test_complete_pinned_interval(self):
        value=summarize(self.data)
        self.assertEqual(value["total_main_commits"], 57)
        self.assertEqual(sum(value["by_intended_effect"].values()), 57)
        self.assertEqual(value["product_or_risk_related_commits"], 30)
    def test_duplicate_commits_are_rejected(self):
        data=copy.deepcopy(self.data)
        data["records"].append(copy.deepcopy(data["records"][0]))
        with self.assertRaisesRegex(ValueError,"duplicate"):
            summarize(data)
    def test_false_hours_are_rejected(self):
        data=copy.deepcopy(self.data)
        data["records"][0]["agent_hours"]=1
        with self.assertRaisesRegex(ValueError,"invent"):
            summarize(data)
    def test_invalid_classification_is_rejected(self):
        data=copy.deepcopy(self.data)
        data["records"][0]["primary_effect"]="zero_value"
        with self.assertRaisesRegex(ValueError,"classification"):
            summarize(data)
if __name__=="__main__":
    unittest.main()
