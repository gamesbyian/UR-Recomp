import tempfile
from pathlib import Path
import unittest
from tools.publish_experiment_result import publish


class ExperimentResultPublisherTests(unittest.TestCase):
    def test_preserves_identity_without_claiming_experiment_success(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = root / "result.json"
            script = root / "input.script"
            summary = root / "summary.md"
            result.write_text('{"changed": 2}')
            script.write_text("BEGIN\n")
            summary.write_text("Two instructions differ.\n")
            report, text = publish(name="jump A/B", question="Does the jump activate code?",
                                   result=result, inputs=[script], summary_md=summary,
                                   metadata={"GITHUB_SHA": "abcdef", "GITHUB_RUN_ID": "123"})
            self.assertEqual(report["status"], "produced_not_adjudicated")
            self.assertEqual(report["conclusion"], "not_adjudicated")
            self.assertEqual(report["source"]["GITHUB_SHA"], "abcdef")
            self.assertEqual(report["integrity"]["input_count"], 1)
            self.assertEqual(len(report["primary"]["sha256"]), 64)
            self.assertIn("Two instructions differ.", text)

    def test_missing_input_rejects_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            primary = root / "result.json"
            primary.write_text("{}")
            with self.assertRaises(ValueError):
                publish(name="test", question="test", result=primary,
                        inputs=[root / "missing"], summary_md=None, metadata={})

    def test_duplicate_and_nonobject_result_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            primary = root / "result.json"
            primary.write_text("[]")
            with self.assertRaises(ValueError):
                publish(name="test", question="test", result=primary,
                        inputs=[], summary_md=None, metadata={})
            primary.write_text("{}")
            with self.assertRaises(ValueError):
                publish(name="test", question="test", result=primary,
                        inputs=[primary], summary_md=None, metadata={})
