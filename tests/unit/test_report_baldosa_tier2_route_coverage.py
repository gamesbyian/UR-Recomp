"""Baldosa Tier-2 cost triage never promotes interpreted PCs or masks QA outcomes."""
from __future__ import annotations
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from report_baldosa_tier2_route_coverage import (
    evaluate, assemble, symbol_index, canonical_usa_pc, BALDOSA_PIN, FIXTURES,
)

D = "a" * 64
IDENTITY = {
    "rom_sha256": "1" * 64,
    "program_digest": "2" * 64,
    "build_digest": "3" * 64,
    "module_id": "pinned-gold",
    "mapper": "lorom",
}
CAPTURE = {
    "identity": IDENTITY,
    "capture_count": 1, "warnings": [],
    "interpreted_instructions": 36, "interpreted_guest_cycles": 250,
    "discoveries": [
        {"candidate_status": "candidate_requires_analysis_and_replay", "variant": "008050:M1X1"},
        {"candidate_status": "unsafe_target", "variant": "008050:M0X1"},
    ],
    "hot_instructions": [
        {"processor": "snes_cpu", "target_pc24": "0x008050", "entry_mx": "M1X1",
         "emulation": 0, "guest_cycles": 200, "interpreted_instructions": 30},
        {"processor": "snes_cpu", "target_pc24": "0x008050", "entry_mx": "M0X1",
         "emulation": 0, "guest_cycles": 50, "interpreted_instructions": 6},
    ],
}

class BaldosaRouteCoverageTests(unittest.TestCase):
    def test_keeps_mode_variants_and_external_leads_only(self):
        symbols = symbol_index([
            {"kind": "function", "address": "808050", "name": "Race_HandleCheckpointFinish"},
            {"kind": "ram", "address": "7E8050", "name": "not_a_function"},
        ])
        result = evaluate("race_1p", CAPTURE, b"real pinned route bytes", symbols, top=1)
        self.assertEqual(result["top_interpreted_pcs"][0]["canonical_usa_pc"], "808050")
        self.assertEqual(result["top_interpreted_pcs"][0]["entry_mx"], "M1X1")
        self.assertEqual(result["top_interpreted_pcs"][0]["guest_cycles"], 200)
        self.assertEqual(result["top_interpreted_pcs"][0]["baldosa_named_function_leads"],
                         ["Race_HandleCheckpointFinish"])
        self.assertFalse(result["top_interpreted_pcs"][0]["source_name_is_verified"])
        self.assertTrue(result["top_truncated"])
        self.assertFalse(result["aot_promotion_authorized"])
        self.assertFalse(result["route_qa_acceptance_proven"])
        self.assertFalse(result["route_capture_binding_verified"])
        self.assertEqual(result["discovery_status_counts"]["unsafe_target"], 1)
        self.assertEqual(canonical_usa_pc(0x7E8050, "lorom"), 0x7E8050)

    def test_keeps_identity_separate_and_does_not_aggregate(self):
        first = evaluate("race_1p", CAPTURE, b"r", {}, top=3)
        second_doc = copy.deepcopy(CAPTURE)
        second_doc["identity"]["build_digest"] = "4" * 64
        second = evaluate("race_2p", second_doc, b"d", {}, top=3)
        report = assemble([first, second])
        self.assertFalse(report["same_build_identity_across_routes"])
        self.assertTrue(report["totals_not_aggregated"])
        self.assertEqual(report["external_source_commit"], BALDOSA_PIN)
        with self.assertRaises(ValueError):
            assemble([first, first])

    def test_incomplete_or_unidentified_capture_is_not_reusable(self):
        bad = copy.deepcopy(CAPTURE)
        bad["identity"].pop("program_digest")
        with self.assertRaisesRegex(ValueError, "program_digest"):
            evaluate("race_1p", bad, b"route", {})
        bad = copy.deepcopy(CAPTURE)
        bad["capture_count"] = 0
        with self.assertRaisesRegex(ValueError, "no completed"):
            evaluate("race_1p", bad, b"route", {})
        bad = copy.deepcopy(CAPTURE)
        bad["warnings"] = ["bounded capture dropped observations"]
        result = evaluate("race_1p", bad, b"route", {})
        self.assertFalse(result["instruction_cost_attribution_complete"])
        self.assertEqual(result["evidence_quality"], "incomplete")
        bad = copy.deepcopy(CAPTURE)
        bad["hot_instructions"][0]["entry_mx"] = "M2X0"
        with self.assertRaisesRegex(ValueError, "M/X"):
            evaluate("race_1p", bad, b"route", {})

    def test_pinned_route_is_present(self):
        self.assertTrue((FIXTURES / "race_1p.txt").is_file())

if __name__ == "__main__":
    unittest.main()
