import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "validate_playtest_report.py"
EXAMPLE = ROOT / "analysis" / "data" / "playtest-report-example.json"

spec = importlib.util.spec_from_file_location("validate_playtest_report", TOOL)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class PlaytestReportValidationTests(unittest.TestCase):
    def load_example(self):
        return json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_canonical_example_is_valid(self):
        report = self.load_example()
        self.assertIs(module.validate_report(report), report)

    def test_personal_identity_fields_are_not_part_of_report_contract(self):
        report = self.load_example()
        report["tester_context"]["name"] = "Tester Name"
        with self.assertRaisesRegex(ValueError, "unknown fields: name"):
            module.validate_report(report)

        report = self.load_example()
        report["tester_context"]["email"] = "tester@example.invalid"
        with self.assertRaisesRegex(ValueError, "unknown fields: email"):
            module.validate_report(report)

    def test_build_artifact_digest_is_strict_lowercase_sha256(self):
        report = self.load_example()
        report["artifact_sha256"] = "A" * 64
        with self.assertRaisesRegex(ValueError, "lowercase SHA-256"):
            module.validate_report(report)

        report = self.load_example()
        report["artifact_sha256"] = "0" * 63
        with self.assertRaisesRegex(ValueError, "lowercase SHA-256"):
            module.validate_report(report)

    def test_unknown_enums_fail_closed(self):
        report = self.load_example()
        report["environment"]["view"] = "Ultrawide"
        with self.assertRaisesRegex(ValueError, "unsupported value"):
            module.validate_report(report)

        report = self.load_example()
        report["finding"]["area"] = "vibes"
        with self.assertRaisesRegex(ValueError, "unsupported value"):
            module.validate_report(report)

    def test_required_reproduction_fields_cannot_be_omitted(self):
        report = self.load_example()
        del report["finding"]["steps"]
        with self.assertRaisesRegex(ValueError, "missing fields: steps"):
            module.validate_report(report)

    def test_free_text_is_bounded_and_canonical(self):
        report = self.load_example()
        report["finding"]["summary"] = " padded "
        with self.assertRaisesRegex(ValueError, "leading/trailing whitespace"):
            module.validate_report(report)

        report = self.load_example()
        report["finding"]["summary"] = "x" * 161
        with self.assertRaisesRegex(ValueError, "exceeds 160 characters"):
            module.validate_report(report)

    def test_file_loader_rejects_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "bad.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cannot read playtest report"):
                module.load_report(path)


if __name__ == "__main__":
    unittest.main()
