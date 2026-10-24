"""Only bounded, complete, exact-path PRs may bypass the full tooling suite."""
import unittest

from tools.ci_select_unit_suite import (
    FOCUSED_TEST_MODULES, OPERATIONS_ONLY, classify, classify_paged, github_mode,
)


def f(path, status="modified"):
    return {"filename": path, "status": status}


class UnitSuiteSelectorTests(unittest.TestCase):
    def test_only_exact_isolated_operations_paths_choose_fast_suite(self):
        for path in sorted(OPERATIONS_ONLY):
            with self.subTest(path=path):
                self.assertEqual(classify([f(path)]), "ops")
        self.assertEqual(classify([f("tools/agent_control.py"),
                                   f("tests/unit/test_agent_control.py")]), "ops")
        self.assertIn("tests.unit.test_agent_control", FOCUSED_TEST_MODULES)
        self.assertIn("tests.unit.test_ci_trigger_policy", FOCUSED_TEST_MODULES)

    def test_any_mixed_or_indirect_change_uses_complete_original_suite(self):
        for path in (
            "tools/report_ci_runtime.py",
            "tools/ci_select_unit_suite.py",
            "tools/strict_vault_manifest.py",
            "tests/unit/test_report_ci_runtime.py",
            ".github/workflows/tooling-unit-tests.yml",
            "docs/RELEASE-QUALITY-LEDGER.json",
            "native/product/modern_root_menu.hpp",
            "analysis/agent-context-lanes.json",
            "docs/operations/MAIN-HISTORY-BACKUP.md",
        ):
            with self.subTest(path=path):
                self.assertEqual(classify([f("tools/agent_control.py"), f(path)]),
                                 "full")

    def test_deleted_renamed_copied_or_unexpected_status_is_never_fast(self):
        for status in ("removed", "renamed", "copied", "changed", None, ""):
            with self.subTest(status=status):
                self.assertEqual(classify([f("tools/agent_control.py", status)]),
                                 "full")
        self.assertEqual(classify([]), "full")
        self.assertEqual(classify([f("tools/agent_control.py")] * 2), "full")
        self.assertEqual(classify([{"status": "modified"}]), "full")
        self.assertEqual(classify([None]), "full")

    def test_full_page_requires_a_second_complete_short_page(self):
        entries = [f("tools/agent_control.py") for _ in range(100)]
        calls = []
        def fetch(page):
            calls.append(page)
            return entries if page == 1 else []
        # One hundred repeated paths are not credible and cannot be fast,
        # even when the next page is empty.
        self.assertEqual(classify_paged(fetch), "full")
        self.assertEqual(calls, [1, 2])
        self.assertEqual(classify_paged(lambda _: entries), "full")

    def test_partial_page_and_invalid_api_response_are_fail_closed(self):
        for payload in (None, {}, {"message": "rate limited"}, "bad",
                        [f("tools/agent_control.py")] * 101):
            with self.subTest(payload=repr(payload)[:35]):
                self.assertEqual(classify_paged(lambda _: payload), "full")

    def test_failed_auth_manual_mode_or_untrusted_repository_defaults_full(self):
        valid = lambda _: [f("tools/agent_control.py")]
        for repo, number, token in (
            ("gamesbyian/UR-Recomp", "", "token"),
            ("gamesbyian/UR-Recomp", "0", "token"),
            ("gamesbyian/UR-Recomp", "1234", ""),
            ("user/other/segments", "1234", "token"),
            ("github.com/a/b", "1234", "token"),
        ):
            with self.subTest(repo=repo, pr=number):
                self.assertEqual(github_mode(repo, number, token, fetch=valid),
                                 "full")
        self.assertEqual(github_mode("gamesbyian/UR-Recomp", "1234", "token",
                                     fetch=valid), "ops")

    def test_transport_denial_chooses_full_with_no_retry(self):
        seen = []
        def denied(page):
            seen.append(page)
            raise ValueError("HTTP 403")
        self.assertEqual(github_mode("gamesbyian/UR-Recomp", "1234",
                                      "token", fetch=denied), "full")
        self.assertEqual(seen, [1])

    def test_same_required_unit_check_has_focused_and_full_execution(self):
        from pathlib import Path
        workflow = Path(".github/workflows/tooling-unit-tests.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("id: unit-scope", workflow)
        self.assertIn("if: steps.unit-scope.outputs.mode == 'ops'", workflow)
        self.assertIn("if: steps.unit-scope.outputs.mode != 'ops'", workflow)
        self.assertIn("python3 tools/ci_select_unit_suite.py", workflow)
        self.assertIn("python3 tools/partition_unit_tests.py", workflow)
        narrow, full = workflow.split(
            "- name: Execute complete operations regression on exactly scoped PRs",
            1,
        )[1].split(
            "- name: Run full dependency-free Python unit tests in timing-balanced shards",
            1,
        )
        self.assertIn("unit-shard0.log", narrow)
        self.assertIn("unit-shard$i.log", full)
        for module in FOCUSED_TEST_MODULES:
            with self.subTest(module=module):
                self.assertIn(module, narrow)

    def test_allowlist_is_only_exact_py_source_and_its_test_modules(self):
        self.assertEqual(len(OPERATIONS_ONLY), 10)
        self.assertEqual(len(FOCUSED_TEST_MODULES), len(set(FOCUSED_TEST_MODULES)))
        self.assertTrue(all(p.endswith(".py") for p in OPERATIONS_ONLY))


if __name__ == "__main__":
    unittest.main()
