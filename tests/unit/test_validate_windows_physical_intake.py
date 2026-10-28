"""Reject malformed offline Windows H01-H07 JSON, never award QA credit."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from tools.validate_windows_physical_intake import (
    RECORDER, SCHEMA, H_IDS, markdown, read_report, source_pins, validate,
)


def fixture():
    return {
        "schema": SCHEMA,
        "authority": "unreviewed_tester_observations_zero_release_credit",
        "candidate": source_pins(RECORDER.read_text(encoding="utf-8")),
        "observed_at_utc": datetime.now(timezone.utc).isoformat(
            timespec="milliseconds").replace("+00:00", "Z"),
        "environment": {
            "setup": "PC-A", "platform": "physical_pc",
            "windows": "Windows 11", "gpu": "GeForce family",
            "monitor": "1920x1080 60Hz", "controllers": "Two USB pads",
            "audio": "Headphones, audible", "launcher": "Explorer",
            "hashCheck": "yes",
        },
        "results": [
            {"id": id, "title": "Human observed case",
             "criteria_label": "reviewer only", "status": "PASS",
             "notes": "Executed the real journey to completion",
             "evidence": id + "-redacted.png"}
            for id in H_IDS
        ],
        "independent_qa_review": "PENDING",
        "official_release_gates_accepted_by_this_report": 0,
        "complete_usa_events_accepted_by_this_report": 0,
        "warning": "No ROM, SRAM, private paths, secrets or unredacted logs.",
    }


class OfflinePhysicalIntakeTests(unittest.TestCase):
    def setUp(self):
        self.pins = source_pins(RECORDER.read_text(encoding="utf-8"))

    def test_source_pins_match_actual_independent_candidate_in_instructions(self):
        instructions = (RECORDER.parent.parent / "WINDOWS-PLAYTEST-INSTRUCTIONS.md"
                        ).read_text(encoding="utf-8")
        self.assertEqual(self.pins["producing_run"], 40763949905)
        self.assertEqual(self.pins["artifact_id"], 12850662557)
        for key in ("source_sha", "inner_zip_sha256", "executable_sha256"):
            self.assertIn(self.pins[key], instructions)

    def test_happy_path_is_structured_but_zero_qa_credit(self):
        data = validate(fixture(), pins=self.pins)
        self.assertTrue(data["format_valid"])
        self.assertTrue(data["physical_pc_claimed"])
        self.assertEqual(data["counts"], {"PASS": 7})
        self.assertEqual(data["triage"], [])
        self.assertFalse(data["independent_qa_accepted"])
        self.assertEqual(data["release_gates_admitted"], 0)
        self.assertEqual(data["complete_original_native_usa_events_admitted"], 0)
        self.assertIn("0/12 release gates", markdown(data))
        self.assertIn("0/45 authentic USA events", markdown(data))

    def test_negative_and_missing_observations_are_not_silenced(self):
        report = fixture()
        report["results"][0]["status"] = "FAIL"
        report["results"][1]["status"] = "BLOCKED"
        report["results"][2]["status"] = "NOT_RUN"
        report["results"][3]["notes"] = ""
        report["environment"]["hashCheck"] = "not_checked"
        report["environment"]["platform"] = "virtual_machine"
        result = validate(report, pins=self.pins)
        msg = " ".join(result["triage"])
        for phrase in ("H01 observed FAIL", "H02 observed BLOCKED",
                       "H04 PASS has no observation", "local inner ZIP",
                       "not a confirmed physical Windows PC", "H04 cannot prove"):
            self.assertIn(phrase, msg)
        self.assertFalse(result["local_inner_zip_exe_hashes_confirmed_by_tester"])
        self.assertFalse(result["independent_qa_accepted"])

    def test_tampering_never_claims_acceptance(self):
        changes = [
            lambda x: x["candidate"].update(source_sha="f" * 40),
            lambda x: x["candidate"].update(inner_zip_sha256="a" * 64),
            lambda x: x.update(authority="release_accepted"),
            lambda x: x.update(independent_qa_review="PASSED"),
            lambda x: x.update(official_release_gates_accepted_by_this_report=True),
            lambda x: x.update(complete_usa_events_accepted_by_this_report=1),
            lambda x: x["results"].pop(),
            lambda x: x["results"][1].update(id="H01"),
            lambda x: x["results"][0].update(status="UNKNOWN"),
            lambda x: x["results"][0].update(evidence="../../private.srm"),
            lambda x: x["environment"].update(platform="imaginary"),
            lambda x: x["environment"].update(hashCheck="guess"),
            lambda x: x.update(schema="future/2"),
            lambda x: x.update(observed_at_utc="2000-99-99Z"),
            lambda x: x.update(unknown="extra"),
        ]
        for action in changes:
            with self.subTest(action=str(action)):
                report = fixture()
                action(report)
                with self.assertRaises(ValueError):
                    validate(report, pins=self.pins)

    def test_json_size_symlink_and_nan_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            report = root / "report.json"
            report.write_text(json.dumps(fixture()), encoding="utf-8")
            self.assertEqual(read_report(report)["schema"], SCHEMA)
            report.write_text('{"value":NaN}')
            with self.assertRaises(ValueError):
                read_report(report)
            report.write_text("X" * 65537)
            with self.assertRaises(ValueError):
                read_report(report)
            link = root / "linked.json"
            link.symlink_to(report)
            with self.assertRaises(ValueError):
                read_report(link)

    def test_duplicate_json_members_rejected_at_all_nesting_levels(self):
        raw = json.dumps(fixture())
        cases = {
            "top-level authority": raw.replace(
                '"authority": "unreviewed_tester_observations_zero_release_credit"',
                '"authority": "release_accepted", '
                '"authority": "unreviewed_tester_observations_zero_release_credit"', 1),
            "nested H01 status": raw.replace(
                '"status": "PASS"', '"status": "FAIL", "status": "PASS"', 1),
            "nested candidate SHA": raw.replace(
                '"source_sha": "', '"source_sha": "' + "f" * 40 +
                '", "source_sha": "', 1),
        }
        with tempfile.TemporaryDirectory() as d:
            report = Path(d) / "duplicate-keys.json"
            for label, content in cases.items():
                with self.subTest(label=label):
                    self.assertNotEqual(content, raw)
                    report.write_text(content, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "malformed JSON"):
                        read_report(report)

    def test_source_pin_parser_rejects_missing_or_repeated_fields(self):
        with self.assertRaises(ValueError):
            source_pins("const candidate = {}")
        source = RECORDER.read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            source_pins(source.replace('source_sha: "', 'source_sha: "' +
                        "f" * 40 + '", source_sha: "', 1))


if __name__ == "__main__":
    unittest.main()
