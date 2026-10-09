"""QA-01 coverage acceptance must never be inferred from static course recovery."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import audit_original_course_event_coverage as audit


class OriginalCourseCensusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(audit.CATALOG.read_text(encoding="utf-8"))
        cls.evidence = json.loads(audit.EVIDENCE.read_text(encoding="utf-8"))

    def test_all_course_families_regions_and_no_false_full_pass(self):
        report = audit.build_census(self.catalog, self.evidence)
        self.assertEqual(report["denominators"], {
            "courses_per_rom": 45,
            "required_region_course_cases": 135,
            "race_circuit_cases": 108,
            "stunt_cases": 27,
            "family_cases_per_region": 9,
        })
        self.assertEqual(report["status_counts"], {"partial": 2, "unverified": 133})
        self.assertEqual(len(report["entries"]), len(set(
            (r["rom"], r["course_id"]) for r in report["entries"]
        )))
        for region in audit.RELEASE_ROMS:
            entries = [r for r in report["entries"] if r["rom"] == region]
            self.assertEqual(len(entries), 45)
            for kind in audit.SLOT_KINDS:
                self.assertEqual(sum(r["event_kind"] == kind for r in entries), 9)
        self.assertEqual(
            [r["course_id"] for r in report["entries"]
             if r["status"] == "partial"],
            ["course:01", "course:20"],
        )

    def test_historical_optimizer_start_x_is_never_promoted_to_runtime_spawn(self):
        report = audit.build_census(self.catalog, self.evidence)
        source = report["historical_start_probes"]
        self.assertEqual(source["classification_counts"], {
            "nonzero_numeric_disagreement": 1,
            "nonzero_numeric_match_only": 42,
            "zero_optimizer_constant_unqualified": 2,
        })
        by_name = {x["name"]: x for x in source["unqualified_and_disagreements"]}
        self.assertEqual(set(by_name), {"Zoom Zoo", "Jumps", "Hill Climb"})
        self.assertEqual(
            (by_name["Zoom Zoo"]["historical_start_x"],
             by_name["Zoom Zoo"]["header_candidate_x16"]),
            (8961, 9200),
        )
        self.assertEqual(
            (by_name["Jumps"]["historical_start_x"],
             by_name["Jumps"]["header_candidate_x16"]),
            (0, 4192),
        )
        self.assertEqual(
            (by_name["Hill Climb"]["historical_start_x"],
             by_name["Hill Climb"]["header_candidate_x16"]),
            (0, 0),
        )
        self.assertTrue(all(not row["runtime_spawn_proven"]
                            for row in by_name.values()))

    def test_dragster_native_only_evidence_does_not_pass_full_course(self):
        report = audit.build_census(self.catalog, self.evidence)
        row = report["entries"][0]
        self.assertEqual(row["status"], "partial")
        self.assertIn("finish", row["expected_events"])
        self.assertIn("lap", row["expected_events"])

    def test_complete_witness_requires_all_events_and_independent_source(self):
        events = {name: "reference_matched" for name in audit.RACE_EVENTS}
        good = dict(
            reference_core="pinned-snes9x",
            candidate_sha="a" * 40,
            rom_sha256="b" * 64,
            reference_run="snes9x-log",
            native_run="native-log",
            input_script="fixture.script",
            result_compared=True,
            fresh_process=True,
            event_observations=events,
        )
        self.assertTrue(audit.validated_witness(good, "race-a"))
        for missing in audit.RACE_EVENTS:
            altered = dict(good, event_observations=dict(events))
            del altered["event_observations"][missing]
            self.assertFalse(audit.validated_witness(altered, "race-a"), missing)
        for key, bad in (("reference_core", "unspecified"),
                         ("fresh_process", False),
                         ("result_compared", False),
                         ("native_run", "")):
            self.assertFalse(audit.validated_witness(dict(good, **{key: bad}), "race-a"))
        self.assertFalse(audit.validated_witness(good, "stunt"))

    def test_fake_pass_missing_runtime_evidence_is_rejected(self):
        bad = dict(self.evidence["observations"][0], status="passed")
        with self.assertRaisesRegex(ValueError, "lacks independent witness"):
            audit.build_census(self.catalog, {"schema_version": 1, "observations": [bad]})
        bad = dict(self.evidence["observations"][0], course_id="course:46")
        with self.assertRaisesRegex(ValueError, "unknown ROM"):
            audit.build_census(self.catalog, {"schema_version": 1, "observations": [bad]})

    def test_duplicate_rows_and_missing_course_fail_closed(self):
        duplicated = [self.evidence["observations"][0]] * 2
        with self.assertRaisesRegex(ValueError, "duplicate"):
            audit.build_census(self.catalog, {"schema_version": 1, "observations": duplicated})
        with self.assertRaisesRegex(ValueError, "45 canonical"):
            audit.validate_catalog({"courses": self.catalog["courses"][:-1]})
        altered = json.loads(json.dumps(self.catalog))
        altered["courses"][2]["resources"]["ids"].append(0x24)
        with self.assertRaisesRegex(ValueError, "checkpoint family"):
            audit.validate_catalog(altered)


if __name__ == "__main__":
    unittest.main()
