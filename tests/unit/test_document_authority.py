"""Current-plan/document ownership guard; historical snapshots are not active queues."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
PRIMARY = ("README.md", "AGENTS.md", "docs/README.md", "docs/PROJECT-PLAN.md",
    "docs/WORK-QUEUE.md", "docs/RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md",
    "docs/BALDOSA-FIRST-CORE-MIGRATION-20261009.md", "docs/QA-BOUNDED-RELEASE-CAMPAIGN.md")
ARCHIVES = (
    "docs/archive/PROJECT-PLAN-THROUGH-20261009.md",
    "docs/archive/WORK-QUEUE-THROUGH-20261009.md",
    "docs/archive/RESOURCE-RESEARCH-PLAN-THROUGH-20261009.md",
    "docs/archive/BALDOSA-MIGRATION-INITIAL-COMPETITION-20261009.md",
)
LINK_RE = re.compile(r"\[[^\]\n]+\]\(([^)\n]+)\)")
LANES = ROOT / "analysis/agent-context-lanes.json"


class CurrentDocumentationAuthoritiesTest(unittest.TestCase):
    def test_active_pages_are_bounded_and_archived_material_is_retained(self):
        budgets = {
            "docs/PROJECT-PLAN.md": 16000,
            "docs/WORK-QUEUE.md": 16000,
            "docs/RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md": 6500,
            "docs/BALDOSA-FIRST-CORE-MIGRATION-20261009.md": 10500,
        }
        for rel, maximum in budgets.items():
            with self.subTest(rel=rel):
                text = (ROOT / rel).read_text(encoding="utf-8")
                self.assertLess(len(text), maximum, rel)
        for rel in ARCHIVES:
            with self.subTest(archive=rel):
                self.assertTrue((ROOT / rel).is_file(), rel)
        self.assertGreater((ROOT / ARCHIVES[0]).stat().st_size, 80000)
        self.assertGreater((ROOT / ARCHIVES[1]).stat().st_size, 100000)

    def test_active_links_resolve(self):
        pages = (*PRIMARY, "docs/archive/README.md", "docs/FRAMEWORK-PIN.md",
            "docs/QA-PLAYER-JOURNEYS.md", "docs/VALIDATION.md",
            "docs/ADVERSARIAL-QA-AND-RELEASE-READINESS.md",
            "docs/WIDESCREEN.md", "docs/PRESENTATION-DENSITY-CONTRACT.md",
            "docs/DISPLAY-PRESENTATION-POLICY.md",
            "docs/MODERN-FRONTEND-SHIPPING-STATUS.md",
            "docs/ORIGINAL-COURSE-EVENT-CENSUS.md")
        for rel in pages:
            path = ROOT / rel
            self.assertTrue(path.exists(), rel)
            for raw in LINK_RE.findall(path.read_text(encoding="utf-8")):
                target = unquote(raw.split("#", 1)[0].split("?", 1)[0])
                if not target or ":" in target.split("/", 1)[0] or target.startswith("/"):
                    continue
                with self.subTest(origin=rel, target=target):
                    candidate = (path.parent / target).resolve()
                    self.assertTrue(candidate.is_relative_to(ROOT), target)
                    self.assertTrue(candidate.is_file(), f"{rel} links missing {target}")

    def test_routes_to_one_live_queue_and_release_ledger(self):
        agent = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        docs_map = (ROOT / "docs/README.md").read_text(encoding="utf-8")
        queue = (ROOT / "docs/WORK-QUEUE.md").read_text(encoding="utf-8")
        for text in (agent, docs_map):
            self.assertIn("WORK-QUEUE.md", text)
        self.assertTrue(queue.startswith("# UR-Recomp: active work queue"))
        self.assertIn("Baldosa", queue)
        self.assertIn("RELEASE-QUALITY-LEDGER.json", docs_map)
        self.assertIn("RELEASE-QUALITY-LEDGER.json", queue)
        ledger = json.loads((ROOT / "docs/RELEASE-QUALITY-LEDGER.json").read_text())
        self.assertEqual(ledger["schema"], "UR-RELEASE-QUALITY-LEDGER/1")
        self.assertEqual(len(ledger["gates"]), 12)

    def test_shared_agent_lanes_have_existing_authorities(self):
        config = json.loads(LANES.read_text())
        for lane in ("baldosa-integration", "release-qa"):
            with self.subTest(lane=lane):
                self.assertIn(lane, config["lanes"])
                authorities = config["lanes"][lane]["authorities"]
                self.assertGreaterEqual(len(authorities), 3)
                self.assertIn("docs/WORK-QUEUE.md", authorities)
                for p in authorities:
                    self.assertTrue((ROOT / p).is_file(), p)


if __name__ == "__main__":
    unittest.main()
