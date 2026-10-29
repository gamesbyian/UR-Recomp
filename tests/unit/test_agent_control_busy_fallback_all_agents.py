"""Every shared-pool worker must retain actionable fallback when its primary is busy.

This intentionally covers all five rotating slots, not just Agent 1, and is
outside the narrow operations-only CI allowlist so changes to dispatch
fallback behavior receive a fresh complete tooling-unit qualification.
"""
import copy
from datetime import date
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from agent_control import BOARD, extract_board, recommend_work


class SharedPoolBusyFallbackAcrossAgentsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = extract_board(BOARD.read_text(encoding="utf-8"))
        cls.cycle = date(2026, 10, 29)

    def test_each_agent_can_fallback_to_free_cohort_when_outside_is_busy(self):
        original = copy.deepcopy(self.board)
        eligible = [job for job in original["work"]
                    if job["state"] in {"ready", "in_review"}]
        cohort = eligible[:5]
        outside_ids = [job["work_id"] for job in eligible[5:]]
        for agent in range(1, 6):
            with self.subTest(agent=agent):
                first = recommend_work(original, agent, self.cycle)
                self.assertEqual(first["candidate_jobs"], cohort)
                busy = [first["first_choice"]["work_id"], *outside_ids]
                report = recommend_work(original, agent, self.cycle, busy)
                expected = next(job for job in cohort
                                if job["work_id"] not in busy)
                self.assertEqual(report["recommended_job"], expected)
                self.assertEqual(report["outside_cohort_fallbacks"], [])
                self.assertEqual(report["busy_work_ids_supplied"], sorted(busy))
        self.assertEqual(self.board, original)

    def test_every_busy_candidate_returns_none_without_fake_lease(self):
        eligible_ids = [job["work_id"] for job in self.board["work"]
                        if job["state"] in {"ready", "in_review"}]
        for agent in range(1, 6):
            with self.subTest(agent=agent):
                result = recommend_work(self.board, agent, self.cycle, eligible_ids)
                self.assertIsNone(result["recommended_job"])
                self.assertEqual(result["candidate_jobs"],
                                 [job for job in self.board["work"]
                                  if job["state"] in {"ready", "in_review"}][:5])

    def test_unbusy_outside_cohort_still_has_precedence(self):
        for agent in range(1, 6):
            with self.subTest(agent=agent):
                first = recommend_work(self.board, agent, self.cycle)
                busy = first["first_choice"]["work_id"]
                result = recommend_work(self.board, agent, self.cycle, [busy])
                self.assertTrue(result["outside_cohort_fallbacks"])
                self.assertIn(result["recommended_job"],
                              result["outside_cohort_fallbacks"])


if __name__ == "__main__":
    unittest.main()
