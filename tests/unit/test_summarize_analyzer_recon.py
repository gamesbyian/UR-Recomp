from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import summarize_analyzer_recon as recon


def node(pc: int, disposition: str, *, reasons=(), demands=(), instructions: int = 1):
    return {
        "key": {"pc24": pc, "m": 1, "x": 1},
        "disposition": disposition,
        "instruction_count": instructions,
        "min_pc24": pc,
        "max_pc24": pc,
        "demands": list(demands),
        "reasons": list(reasons),
        "digest": "",
    }


class AnalyzerReconSummaryTests(unittest.TestCase):
    def test_summarizes_aot_lle_and_runtime_edges(self) -> None:
        manifest = {
            "format_version": 3,
            "roots": [{"pc24": 0x808000, "m": 1, "x": 1}],
            "exit_modes": {"80:8000:M1X1": {"m": 1, "x": 1}},
            "exit_mode_sets": {},
            "nodes": {
                "80:8000:M1X1": node(
                    0x808000,
                    "aot_eligible",
                    instructions=3,
                    demands=[
                        {
                            "site_pc24": 0x808010,
                            "kind": "direct_call",
                            "resolution": "aot_exact",
                            "target": {"pc24": 0x818000, "m": 1, "x": 1},
                            "detail": "",
                        },
                        {
                            "site_pc24": 0x808020,
                            "kind": "unresolved_indirect",
                            "resolution": "lle_dynamic",
                            "target": None,
                            "detail": "pointer target unknown",
                        },
                    ],
                ),
                "81:8000:M1X1": node(
                    0x818000,
                    "lle_only",
                    reasons=["analysis_budget"],
                    instructions=2,
                ),
            },
        }

        report = recon.summarize_manifest(manifest)
        self.assertEqual(report["roots"], 1)
        self.assertEqual(report["nodes"]["total"], 2)
        self.assertEqual(report["nodes"]["aot_capable"], 1)
        self.assertEqual(report["nodes"]["lle_only"], 1)
        self.assertEqual(report["nodes"]["aot_capable_fraction"], 0.5)
        self.assertEqual(report["nodes"]["decoded_instruction_instances"], 5)
        self.assertEqual(report["edges"]["by_kind"]["direct_call"], 1)
        self.assertEqual(report["edges"]["runtime_or_unresolved_count"], 1)
        self.assertEqual(
            report["edges"]["runtime_or_unresolved"][0]["site_pc"], "80:8020"
        )
        self.assertEqual(report["lle"]["reason_counts"]["analysis_budget"], 1)

    def test_rejects_wrong_manifest_version(self) -> None:
        with self.assertRaises(ValueError):
            recon.summarize_manifest({"format_version": 2, "nodes": {"x": {}}})

    def test_rejects_empty_manifest(self) -> None:
        with self.assertRaises(ValueError):
            recon.summarize_manifest({"format_version": 3, "nodes": {}})


if __name__ == "__main__":
    unittest.main()
