"""Draft feedback is cheap and non-authoritative; ready PR tests remain full."""
import unittest

from tools.ci_draft_target_tests import (
    MAX_MODULES, MAX_ESTIMATED_SECONDS, census, github_census, select,
)


def item(path, state="modified"):
    return {"filename": path, "status": state}


class DraftTargetTests(unittest.TestCase):
    def setUp(self):
        self.available = {
            "test_qa01_rf071_getter_vs_script_dump",
            "test_agent_control", "test_ci_trigger_policy",
            "test_tooling_unit_workflow_contract", "test_run_unit_shard",
            "test_ci_draft_target_tests", "test_expensive",
        }
        self.costs = {"tests.unit." + n: 0.1 for n in self.available}
        self.costs["tests.unit.test_expensive"] = 12.0

    def test_exact_tests_and_tools_are_related(self):
        changed = {
            "tools/qa01_rf071_getter_vs_script_dump.py",
            "tests/unit/test_ci_draft_target_tests.py",
        }
        result = select(changed, self.costs, self.available)
        self.assertEqual(result, [
            "tests.unit.test_ci_draft_target_tests",
            "tests.unit.test_qa01_rf071_getter_vs_script_dump",
        ])
        self.assertEqual(len(result), len(set(result)))

    def test_workflow_policy_and_self_contract(self):
        result = select({
            ".github/workflows/tooling-unit-tests.yml",
            "docs/OTHER-DOC.md",
        }, self.costs, self.available)
        self.assertEqual(result, ["tests.unit.test_ci_trigger_policy",
                                  "tests.unit.test_tooling_unit_workflow_contract"])
        self.assertEqual(select({".github/workflows/qa01-event-campaign.yml"},
                                self.costs, self.available),
                         ["tests.unit.test_ci_trigger_policy"])

    def test_ineligible_does_not_claim_coverage(self):
        cases = (
            {"native/product/modern_root_menu.hpp"},
            {"docs/UNRELATED.md"},
            {"tools/does_not_exist.py"},
        )
        for changed in cases:
            self.assertEqual(select(changed, self.costs, self.available), [])
        self.assertEqual(select(None, self.costs, self.available), [])

    def test_never_run_known_expensive_module_as_quick_check(self):
        self.assertEqual(select({"tests/unit/test_expensive.py"},
                                self.costs, self.available), [])

    def test_bounded_predicted_budget_and_module_count(self):
        names = ["test_a", "test_b", "test_c", "test_d",
                 "test_e", "test_f", "test_g", "test_h"]
        costs = {"tests.unit." + n: 3.0 for n in names}
        result = select({"tests/unit/" + n + ".py" for n in names},
                        costs, set(names))
        self.assertLessEqual(len(result), MAX_MODULES)
        self.assertLessEqual(sum(costs[name] for name in result),
                             MAX_ESTIMATED_SECONDS)
        self.assertEqual(len(result), 4)

    def test_new_unknown_module_has_bounded_fallback_estimate(self):
        self.assertEqual(select({"tests/unit/test_new.py"}, {},
                                {"test_new"}), ["tests.unit.test_new"])

    def test_complete_pr_census_fails_closed(self):
        self.assertEqual(census(lambda _: [item("tools/a.py")]), {"tools/a.py"})
        self.assertIsNone(census(lambda _: []))
        self.assertIsNone(census(lambda _: {"message": "denied"}))
        self.assertIsNone(census(lambda _: [item("tools/a.py", "renamed")]))
        self.assertIsNone(census(lambda _: [item("tools/a.py")] * 2))
        self.assertIsNone(census(lambda _: [item("tools/a.py")] * 100))
        self.assertIsNone(census(lambda _: [item("tools/a.py", "removed")]))
        seen = []
        def pages(i):
            seen.append(i)
            if i == 1:
                return [item("tools/m%d.py" % n) for n in range(100)]
            return [item("tests/unit/test_a.py")]
        self.assertEqual(len(census(pages)), 101)
        self.assertEqual(seen, [1, 2])
        def transport(_):
            raise OSError("API offline")
        self.assertIsNone(census(transport))

    def test_github_metadata_rejects_bad_scope(self):
        def f(_):
            return [item("tests/unit/test_agent_control.py")]
        for repo, pr, token in (
            ("../evil/repo", "12", "x"),
            ("gamesbyian/UR-Recomp", "-1", "x"),
            ("gamesbyian/UR-Recomp", "12", ""),
        ):
            self.assertIsNone(github_census(repo, pr, token, fetch=f))
        self.assertEqual(github_census("gamesbyian/UR-Recomp", "12", "x", fetch=f),
                         {"tests/unit/test_agent_control.py"})

    def test_empty_census_emits_no_phantom_unittest_module(self):
        import contextlib
        import io
        from unittest.mock import patch
        from tools.ci_draft_target_tests import main

        output = io.StringIO()
        # No token means a fail-closed, empty PR census, as can happen during
        # a draft check. Bash mapfile must receive zero lines, not one blank.
        with patch.dict("os.environ", {"GITHUB_TOKEN": "",
                                       "GH_PR_NUMBER": ""}):
            with contextlib.redirect_stdout(output):
                main()
        self.assertEqual(output.getvalue(), "")

    def test_workflow_retains_ready_full_suite_and_draft_label(self):
        from pathlib import Path
        text = Path(".github/workflows/tooling-unit-tests.yml").read_text()
        self.assertIn("github.event.pull_request.draft == false", text)
        self.assertIn("Run full dependency-free Python unit tests", text)
        self.assertIn("DRAFT_TARGETED_DIAGNOSTIC_ONLY", text)
        self.assertIn("python3 tools/ci_draft_target_tests.py", text)
        self.assertIn("timeout 45s python3 -m unittest", text)


if __name__ == "__main__":
    unittest.main()
