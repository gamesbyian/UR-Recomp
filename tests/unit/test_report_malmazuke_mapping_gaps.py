"""Pure unit contracts for pinned malmazuke structural gap triage, not release QA."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from report_malmazuke_mapping_gaps import build_report, render_markdown
from query_malmazuke_symbols import PIN, load_inputs


class MalmazukeStructuralGapTests(unittest.TestCase):
    def test_status_accounting_and_pinned_research(self):
        links = {"schema_version": 1, "source": {"commit": PIN}, "entries": [
            {"pal": "80:8100", "domains": ["result"], "pal_symbol_class": "observed",
             "mark_native": ["src/core/result.cpp:draw"],
             "correspondence": {"status": "not-covered"}},
            {"pal": "81:8050", "domains": ["progress", "result"], "pal_symbol_class": "observed",
             "mark_native": ["src/core/race_progress.cpp:update_checkpoints"],
             "correspondence": {"status": "structural-interval-candidate", "usa": "81:8050"}},
            {"pal": "83:9000", "domains": ["frontend"], "pal_symbol_class": "unknown",
             "mark_native": [], "correspondence": {"status": "data-interval-only"}},
        ]}
        labels = [{"address": "$80:8100", "class": "observed",
                   "source_records": ["docs/research/R-0057-one-run-result.md"]}]
        r = build_report(links, labels, limit=1)
        self.assertEqual(r["counts"]["selected_unique_pal_addresses"], 3)
        self.assertEqual(r["counts"]["not-covered"], 1)
        self.assertEqual(r["by_domain"]["result"]["total"], 2)
        self.assertEqual(r["by_domain"]["result"]["not-covered"], 1)
        self.assertEqual(r["by_domain"]["progress"]["structural-interval-candidate"], 1)
        self.assertEqual(r["worklist"][0]["source_records"],
                         ["docs/research/R-0057-one-run-result.md"])
        self.assertIsNone(r["worklist"][0]["usa_candidate"])
        self.assertFalse(r["worklist"][0]["verified_usa_semantics"])
        self.assertIn("not an absent implementation", r["interpretation"])
        self.assertIn("result", render_markdown(r))
        self.assertEqual(build_report(links, labels, domains=("result",))["counts"]["selected_unique_pal_addresses"], 2)
        with self.assertRaises(ValueError):
            build_report(links, labels, domains=("missing-domain",))
        with self.assertRaises(ValueError):
            build_report(links, labels, limit=0)

    def test_real_frozen_domain_counts(self):
        try:
            _symbols, links, labels = load_inputs()
        except FileNotFoundError:
            self.skipTest("pinned imported source not in sparse checkout")
        r = build_report(links, labels, domains=("result",), limit=3)
        self.assertEqual(r["by_domain"]["result"]["total"], 150)
        self.assertEqual(r["by_domain"]["result"]["not-covered"], 148)
        self.assertEqual(r["counts"]["selected_unique_pal_addresses"], 150)
        self.assertEqual(len(r["worklist"]), 3)
        self.assertTrue(r["worklist_truncated"])
        self.assertTrue(all(e["status"] == "not-covered" for e in r["worklist"]))


if __name__ == "__main__":
    unittest.main()
