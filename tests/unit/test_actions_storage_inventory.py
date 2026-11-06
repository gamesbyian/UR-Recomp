"""Offline, no-auth controls for the read-only account artifact census."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from tools import actions_storage_inventory as inv


def a(ident, name, size, expired=False):
    return {
        "id": ident, "name": name, "size_in_bytes": size,
        "created_at": "2026-11-01T00:00:00Z",
        "expires_at": "2026-11-14T00:00:00Z",
        "expired": expired,
    }


class InventoryTests(unittest.TestCase):
    def test_multiple_pages_complete_and_grouped(self):
        items = [a(i + 1, "atlas" if i < 100 else "receipt", 100) for i in range(101)]
        def api(*argv):
            page = int(argv[-1].split("page=")[-1])
            return {"total_count": 101, "artifacts": items[(page - 1) * 100:page * 100]}
        listed = inv.artifact_inventory("gamesbyian/Glimpse", api=api)
        self.assertEqual(len(listed), 101)
        summary = inv.summarize("gamesbyian/Glimpse", listed,
                                now=datetime(2026, 11, 2, tzinfo=timezone.utc))
        self.assertEqual(summary["current_artifact_bytes_estimate"], 10100)
        self.assertEqual(summary["largest_name_groups"][0]["count"], 100)

    def test_ur_small_page_complete_and_rechecked(self):
        items = [a(i + 1, "receipt", i + 1) for i in range(51)]
        called = []
        def api(*argv):
            q = argv[-1]
            self.assertIn("per_page=25", q)
            n = int(q.split("page=")[-1])
            called.append(n)
            return {"total_count": len(items),
                    "artifacts": items[(n - 1) * 25:n * 25]}
        rows = inv.artifact_inventory("gamesbyian/UR-Recomp", api=api,
                                      max_pages=400, page_size=25,
                                      recheck_first_page=True)
        self.assertEqual(len(rows), 51)
        self.assertEqual(called, [1, 2, 3, 1])

    def test_ur_parallel_pages_keep_exact_completeness_and_ids(self):
        items = [a(i + 1, "qa01-receipt", i + 1) for i in range(76)]
        calls = []
        def api(*argv):
            q = argv[-1]
            self.assertIn("per_page=25", q)
            page = int(q.split("page=")[-1])
            calls.append(page)
            return {"total_count": len(items),
                    "artifacts": items[(page - 1) * 25:page * 25]}
        result = inv.artifact_inventory(
            "gamesbyian/UR-Recomp", api=api, page_size=25, max_pages=400,
            recheck_first_page=True, workers=4)
        self.assertEqual([x["id"] for x in result], list(range(1, 77)))
        self.assertEqual(calls[0], 1)
        self.assertEqual(calls[-1], 1)
        self.assertEqual(sorted(calls[1:-1]), [2, 3, 4])

    def test_ur_parallel_exact_multiple_checks_empty_terminal_page(self):
        items = [a(i + 1, "receipt", 9) for i in range(50)]
        calls = []
        def api(*argv):
            page = int(argv[-1].split("page=")[-1])
            calls.append(page)
            return {"total_count": 50, "artifacts": items[(page - 1) * 25:page * 25]}
        found = inv.artifact_inventory("gamesbyian/UR-Recomp", api=api,
                                      page_size=25, workers=2,
                                      recheck_first_page=True)
        self.assertEqual(len(found), 50)
        self.assertIn(3, calls)
        self.assertEqual(calls[-1], 1)

    def test_ur_parallel_changed_total_still_fails_closed(self):
        items = [a(i + 1, "receipt", 1) for i in range(26)]
        def api(*argv):
            n = int(argv[-1].split("page=")[-1])
            return {"total_count": 26 if n == 1 else 27,
                    "artifacts": items[(n - 1) * 25:n * 25]}
        with self.assertRaisesRegex(RuntimeError, "count changed"):
            inv.artifact_inventory("gamesbyian/UR-Recomp", api=api,
                                   page_size=25, workers=4)

    def test_ur_parallel_duplicate_id_still_fails_closed(self):
        items = [a(i + 1, "receipt", 1) for i in range(26)]
        items[25]["id"] = items[0]["id"]
        def api(*argv):
            n = int(argv[-1].split("page=")[-1])
            return {"total_count": 26,
                    "artifacts": items[(n - 1) * 25:n * 25]}
        with self.assertRaisesRegex(RuntimeError, "duplicate artifact"):
            inv.artifact_inventory("gamesbyian/UR-Recomp", api=api,
                                   page_size=25, workers=4)

    def test_ur_first_page_drift_fails_closed(self):
        items = [a(i + 1, "receipt", 1) for i in range(26)]
        count = 0
        def api(*argv):
            nonlocal count
            count += 1
            n = int(argv[-1].split("page=")[-1])
            if count == 3:
                return {"total_count": 26,
                        "artifacts": [a(999, "new", 1), *items[:24]]}
            return {"total_count": 26,
                    "artifacts": items[(n - 1) * 25:n * 25]}
        with self.assertRaisesRegex(RuntimeError, "first page changed"):
            inv.artifact_inventory("gamesbyian/UR-Recomp", api=api,
                                   page_size=25, recheck_first_page=True)

    def test_invalid_page_options_rejected_before_network(self):
        def no_network(*_):
            self.fail("invalid arguments should not call GitHub")
        for bad in (0, True, 10, 101, "25", None):
            with self.subTest(page_size=bad), self.assertRaises(ValueError):
                inv.artifact_inventory("gamesbyian/UR-Recomp", api=no_network,
                                       page_size=bad)
        with self.assertRaises(ValueError):
            inv.artifact_inventory("gamesbyian/UR-Recomp", api=no_network,
                                   page_size=25, recheck_first_page=1)
        for invalid in (0, 3, True, "4", None):
            with self.subTest(workers=invalid), self.assertRaises(ValueError):
                inv.artifact_inventory("gamesbyian/UR-Recomp", api=no_network,
                                       page_size=25, workers=invalid)

    def test_refuse_partial_inventory(self):
        def api(*argv):
            return {"total_count": 2, "artifacts": [a(1, "only", 3)]}
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            inv.artifact_inventory("gamesbyian/Chunks", api=api)

    def test_refuse_changed_count_between_pages(self):
        def api(*argv):
            page = int(argv[-1].split("page=")[-1])
            return {"total_count": 101 if page == 1 else 100,
                    "artifacts": [a(i + 1, "x", 1) for i in range(100)] if page == 1 else []}
        with self.assertRaisesRegex(RuntimeError, "changed"):
            inv.artifact_inventory("gamesbyian/Chunks", api=api)

    def test_expired_does_not_count_as_current(self):
        summary = inv.summarize(
            "gamesbyian/AYA", [a(1, "old", 1_000, True), a(2, "new", 4)],
            now=datetime(2026, 11, 2, tzinfo=timezone.utc))
        self.assertEqual(summary["expired_count"], 1)
        self.assertEqual(summary["current_artifact_bytes_estimate"], 4)

    def test_invalid_page_and_names_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "repository"):
            inv.artifact_inventory("not a repo")
        with self.assertRaisesRegex(ValueError, "identifier"):
            inv.artifact_inventory("gamesbyian/Glimpse", api=lambda *_: {
                "total_count": 1, "artifacts": [dict(a(1, "x", 3), id=0)]})
        with self.assertRaisesRegex(ValueError, "timestamp"):
            inv.parse_date("2026-11-02")

    def test_output_names_are_escaped(self):
        result = inv.summarize("gamesbyian/Glimpse", [a(1, "a|b", 4)],
                               now=datetime(2026, 11, 2, tzinfo=timezone.utc))
        self.assertIn("a\\|b", inv.markdown([result]))


    def test_gh_json_retries_503_then_returns_json(self):
        failed = SimpleNamespace(returncode=1, stderr="gh: upstream (HTTP 503) secret=never-log", stdout="")
        passed = SimpleNamespace(returncode=0, stderr="", stdout='{"ok": true}')
        with patch.object(inv.subprocess, "run", side_effect=[failed, passed]) as run:
            with patch.object(inv.time, "sleep") as sleep:
                self.assertEqual(inv.gh_json("api", "repos/gamesbyian/UR-Recomp/actions/artifacts"), {"ok": True})
        self.assertEqual(run.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_gh_json_retries_bounded_truncated_artifact_json(self):
        bad = SimpleNamespace(returncode=1, stderr="unexpected end of JSON input token=never-log", stdout="")
        good = SimpleNamespace(returncode=0, stderr="", stdout='{"total_count":0,"artifacts":[]}')
        with patch.object(inv.subprocess, "run", side_effect=[bad, good]) as run:
            with patch.object(inv.time, "sleep") as sleep:
                got = inv.gh_json("api", "repos/gamesbyian/UR-Recomp/actions/artifacts")
        self.assertEqual(got["total_count"], 0)
        self.assertEqual(run.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_gh_json_auth_denial_has_status_only_and_no_retry(self):
        failed = SimpleNamespace(returncode=1, stderr="gh: token=secret (HTTP 403)", stdout="")
        with patch.object(inv.subprocess, "run", return_value=failed) as run:
            with patch.object(inv.time, "sleep") as sleep:
                with self.assertRaisesRegex(RuntimeError, "HTTP 403") as caught:
                    inv.gh_json("api", "repos/gamesbyian/UR-Recomp/actions/artifacts")
        self.assertNotIn("secret", str(caught.exception))
        run.assert_called_once()
        sleep.assert_not_called()

    def test_gh_json_bounded_rate_limit_retry(self):
        failed = SimpleNamespace(returncode=1, stderr="gh: rate limit (HTTP 429)", stdout="")
        with patch.object(inv.subprocess, "run", return_value=failed) as run:
            with patch.object(inv.time, "sleep") as sleep:
                with self.assertRaisesRegex(RuntimeError, "HTTP 429"):
                    inv.gh_json("api", "repos/gamesbyian/UR-Recomp/actions/artifacts")
        self.assertEqual(run.call_count, 3)
        self.assertEqual([c.args for c in sleep.call_args_list], [(1,), (2,)])


if __name__ == "__main__":
    unittest.main()
