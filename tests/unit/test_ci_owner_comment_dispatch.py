"""Real data-bound authorization and no-dispatch regressions (no GitHub writes)."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from ci_owner_comment_dispatch import (intent, exact_head, process, active_run_id,
    science_intent, recent_science_run, science_process, SCIENCE_WORKFLOW)

REPO = "gamesbyian/UR-Recomp"
SHA = "a" * 40


def event(workflow="tooling-unit-tests.yml", text=None):
    return {"action": "created", "repository": {"full_name": REPO},
            "issue": {"number": 2837, "pull_request": {"url": "pr"}},
            "comment": {"body": text if text is not None else "/ur-ci run " + workflow + " " + SHA,
                        "user": {"login": "gamesbyian"}, "author_association": "OWNER"}}


def pr():
    return {"number": 2837, "state": "open", "draft": False,
            "head": {"repo": {"full_name": REPO}, "sha": SHA,
                     "ref": "ops/test-ref"}}


class OwnerCommentDispatchTests(unittest.TestCase):
    def test_two_allowlisted_workflows_and_exact_head(self):
        for name in ("tooling-unit-tests.yml", "ghost-target-native-acceptance.yml"):
            with self.subTest(name=name):
                calls = []
                outcome = process(event(name), REPO, "gamesbyian",
                    lambda n: (calls.append(("get", n)), pr())[1],
                    lambda w, ref: (calls.append(("census", w, ref)),
                                    {"workflow_runs": [], "total_count": 0})[1],
                    lambda w, ref: calls.append(("dispatch", w, ref)))
                self.assertEqual(calls, [("get", 2837),
                                         ("census", name, "ops/test-ref"),
                                         ("dispatch", name, "ops/test-ref")])
                self.assertEqual(outcome[2], SHA)
                self.assertIsNone(outcome[4])

    def test_noncommands_and_edited_or_nonpr_comments_never_hit_api(self):
        for body in ("just a normal comment", "/ur-ci run arbitrary.yml " + SHA,
                     "/ur-ci run tooling-unit-tests.yml b",
                     "/ur-ci run tooling-unit-tests.yml " + SHA + " extra"):
            self.assertIsNone(process(event(text=body), REPO, "gamesbyian",
                lambda _: self.fail("queried PR on noncommand"),
                lambda *args: self.fail("read runs on noncommand"),
                lambda *args: self.fail("dispatched noncommand")))
        e = event()
        e["action"] = "edited"
        self.assertIsNone(intent(e, REPO, "gamesbyian"))
        e = event()
        e["issue"]["pull_request"] = None
        self.assertIsNone(intent(e, REPO, "gamesbyian"))

    def test_untrusted_commanders_are_rejected_before_pr_query(self):
        for key, value in (("author_association", "CONTRIBUTOR"),
                           ("user", {"login": "stranger"})):
            e = event()
            e["comment"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                process(e, REPO, "gamesbyian",
                    lambda _: self.fail("queried untrusted PR"),
                    lambda *args: self.fail("read runs on untrusted PR"),
                    lambda *args: self.fail("dispatched untrusted"))
        e = event()
        e["repository"]["full_name"] = "other/repo"
        with self.assertRaises(ValueError):
            intent(e, REPO, "gamesbyian")

    def test_draft_closed_fork_changed_sha_unsafe_ref_all_fail_before_dispatch(self):
        for field, value in (("sha", "b" * 40), ("ref", "main"),
                             ("ref", "bad/../main"), ("ref", "bad//name"),
                             ("ref", "-bad"), ("repo", {"full_name": "fork/repo"})):
            p = pr()
            p["head"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                process(event(), REPO, "gamesbyian",
                    lambda _: p,
                    lambda *args: self.fail("read runs on invalid PR"),
                    lambda *args: self.fail("dispatched invalid PR"))
        for field, value in (("state", "closed"), ("draft", True)):
            p = pr()
            p[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                exact_head(p, 2837, REPO, SHA)

    def test_preexisting_unchanged_inflight_qualification_is_not_restarted(self):
        for state in ("queued", "in_progress", "pending", "waiting", "requested"):
            with self.subTest(state=state):
                seen = []
                def census(w, ref):
                    seen.append((w, ref))
                    return {"total_count": 1, "workflow_runs": [{
                        "id": 12345, "event": "workflow_dispatch",
                        "head_branch": "ops/test-ref", "head_sha": SHA,
                        "status": state}]}
                outcome = process(event(), REPO, "gamesbyian", lambda _: pr(),
                                  census, lambda *args: self.fail("duplicate dispatch"))
                self.assertEqual(outcome[4], 12345)
                self.assertEqual(seen, [("tooling-unit-tests.yml", "ops/test-ref")])

    def test_completed_or_other_source_only_may_dispatch(self):
        for status, sha in (("completed", SHA), ("in_progress", "b" * 40)):
            sent = []
            outcome = process(event(), REPO, "gamesbyian", lambda _: pr(),
                 lambda w, r: {"total_count": 1, "workflow_runs": [{
                     "id": 12345, "event": "workflow_dispatch",
                     "head_branch": "ops/test-ref", "head_sha": sha,
                     "status": status}]},
                 lambda w, r: sent.append((w, r)))
            self.assertIsNone(outcome[4])
            self.assertEqual(sent, [("tooling-unit-tests.yml", "ops/test-ref")])

    def test_missing_or_partial_workflow_census_fails_closed(self):
        for reply in (None, {}, {"workflow_runs": [], "total_count": 1},
                      {"workflow_runs": [{"id": 1}], "total_count": 2},
                      {"workflow_runs": [{}], "total_count": 1.5}):
            with self.subTest(reply=reply), self.assertRaises(ValueError):
                process(event(), REPO, "gamesbyian", lambda _: pr(),
                        lambda w, r: reply,
                        lambda *args: self.fail("dispatched without trustworthy census"))

    def test_owner_hp_science_command_requests_current_main_without_pr_source(self):
        clock = datetime(2026, 11, 1, 2, 15, tzinfo=timezone.utc)
        calls = []
        outcome = science_process(event(text="/ur-ci hp-research"), REPO,
            "gamesbyian", lambda: (calls.append("repo"),
                {"full_name": REPO, "default_branch": "main", "archived": False})[1],
            lambda w, ref: (calls.append(("census", w, ref)),
                           {"workflow_runs": [], "total_count": 0})[1],
            lambda w, ref: calls.append(("dispatch", w, ref)), clock)
        self.assertEqual(outcome, (2837, SCIENCE_WORKFLOW, None))
        self.assertEqual(calls, ["repo", ("census", SCIENCE_WORKFLOW, "main"),
                                 ("dispatch", SCIENCE_WORKFLOW, "main")])
        wf = Path(".github/workflows/owner-comment-ci-dispatch.yml").read_text()
        self.assertIn("startsWith(github.event.comment.body, '/ur-ci hp-research')", wf)
        self.assertIn("github.event.comment.user.login == github.repository_owner", wf)
        self.assertIn("github.event.comment.author_association == 'OWNER'", wf)
        self.assertIn("persist-credentials: false", wf)
        self.assertIn("actions: write", wf)
        science = Path(".github/workflows/owner-hp-seeded-2p-research.yml").read_text()
        self.assertIn("  workflow_dispatch:", science)
        self.assertIn("  schedule:", science)
        self.assertIn("github.ref == 'refs/heads/main'", science)
        self.assertIn("run_on_hp: true", science)
        self.assertIn("hp_seeded_2p: true", science)

    def test_hp_science_comment_ignores_noncommands_and_rejects_untrusted(self):
        clock = datetime(2026, 11, 1, 2, 15, tzinfo=timezone.utc)
        for value in ("normal message", "/ur-ci hp-research unexpected",
                      "/ur-ci run hp-research", "/ur-ci hp-research " + SHA):
            with self.subTest(command=value):
                self.assertIsNone(science_process(event(text=value), REPO,
                    "gamesbyian", lambda: self.fail("noncommand queried repo"),
                    lambda *args: self.fail("noncommand queried runs"),
                    lambda *args: self.fail("noncommand dispatched"), clock))
        e = event(text="/ur-ci hp-research")
        e["action"] = "edited"
        self.assertIsNone(science_intent(e, REPO, "gamesbyian"))
        e = event(text="/ur-ci hp-research")
        e["issue"]["pull_request"] = None
        self.assertIsNone(science_intent(e, REPO, "gamesbyian"))
        for key, value in (("author_association", "CONTRIBUTOR"),
                           ("user", {"login": "stranger"})):
            e = event(text="/ur-ci hp-research")
            e["comment"][key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                science_process(e, REPO, "gamesbyian",
                    lambda: self.fail("untrusted queried repo"),
                    lambda *args: self.fail("untrusted queried runs"),
                    lambda *args: self.fail("untrusted dispatched"), clock)
        e = event(text="/ur-ci hp-research")
        e["repository"]["full_name"] = "somebody/else"
        with self.assertRaises(ValueError):
            science_intent(e, REPO, "gamesbyian")

    def test_hp_science_refuses_nonmain_archived_or_unverified_repository(self):
        clock = datetime(2026, 11, 1, 2, 15, tzinfo=timezone.utc)
        for info in (None, {}, {"full_name": "other/repo",
                                  "default_branch": "main", "archived": False},
                     {"full_name": REPO, "default_branch": "development",
                      "archived": False},
                     {"full_name": REPO, "default_branch": "main",
                      "archived": True}):
            with self.subTest(repo=info), self.assertRaises(ValueError):
                science_process(event(text="/ur-ci hp-research"), REPO,
                    "gamesbyian", lambda: info,
                    lambda *args: self.fail("untrusted repo queried runs"),
                    lambda *args: self.fail("untrusted repo dispatched"), clock)

    def test_hp_science_suppresses_active_and_recent_accepted_or_failed_runs(self):
        clock = datetime(2026, 11, 1, 2, 15, tzinfo=timezone.utc)
        def row(*, rid=200, status="completed", age=30, event_type="schedule"):
            return {"id": rid, "event": event_type, "status": status,
                    "head_branch": "main", "head_sha": SHA,
                    "created_at": (clock - timedelta(minutes=age)).isoformat()}
        for outcome in (row(), row(status="queued", age=300),
                        row(status="in_progress", age=180),
                        row(status="completed", age=75, event_type="workflow_dispatch"),
                        row(status="completed", age=25, event_type="workflow_dispatch")):
            with self.subTest(observation=outcome):
                result = science_process(event(text="/ur-ci hp-research"),
                    REPO, "gamesbyian",
                    lambda: {"full_name": REPO, "default_branch": "main",
                             "archived": False},
                    lambda w, ref: {"workflow_runs": [outcome], "total_count": 1},
                    lambda *args: self.fail("duplicate HP science request"), clock)
                self.assertEqual(result[2], outcome["id"])
        old = row(age=100, status="completed")
        called = []
        result = science_process(event(text="/ur-ci hp-research"),
            REPO, "gamesbyian",
            lambda: {"full_name": REPO, "default_branch": "main", "archived": False},
            lambda w, ref: {"workflow_runs": [old], "total_count": 1},
            lambda w, ref: called.append((w, ref)), clock)
        self.assertEqual(called, [(SCIENCE_WORKFLOW, "main")])
        self.assertIsNone(result[2])

    def test_hp_science_malformed_or_truncated_census_fails_closed(self):
        clock = datetime(2026, 11, 1, 2, 15, tzinfo=timezone.utc)
        good = {"id": 200, "event": "schedule", "status": "completed",
                "head_branch": "main", "head_sha": SHA,
                "created_at": (clock - timedelta(hours=3)).isoformat()}
        for reply in (None, {}, {"workflow_runs": [], "total_count": 1},
                      {"workflow_runs": [good], "total_count": 2},
                      {"workflow_runs": [good], "total_count": 0},
                      {"workflow_runs": [dict(good, id=True)], "total_count": 1},
                      {"workflow_runs": [dict(good, head_branch="evil")], "total_count": 1},
                      {"workflow_runs": [dict(good, head_sha="bad")], "total_count": 1},
                      {"workflow_runs": [dict(good, event="push")], "total_count": 1},
                      {"workflow_runs": [dict(good, status="magic")], "total_count": 1},
                      {"workflow_runs": [dict(good, created_at=clock.isoformat())],
                       "total_count": 1}):
            if isinstance(reply, dict) and reply.get("workflow_runs"):
                if reply["workflow_runs"][0].get("created_at") == clock.isoformat():
                    reply["workflow_runs"][0]["created_at"] = (
                        clock + timedelta(seconds=1)).isoformat()
            with self.subTest(reply=reply), self.assertRaises(ValueError):
                science_process(event(text="/ur-ci hp-research"), REPO,
                    "gamesbyian",
                    lambda: {"full_name": REPO, "default_branch": "main",
                             "archived": False},
                    lambda w, ref: reply,
                    lambda *args: self.fail("malformed census dispatched"), clock)
        recent = dict(good, created_at=(clock - timedelta(minutes=5)).isoformat())
        with self.assertRaises(ValueError):
            recent_science_run({"workflow_runs": [good, recent],
                                "total_count": 2}, clock)

    def test_hp_science_comments_serialize_across_distinct_prs(self):
        """One global HP dispatch lock, preserving per-PR exact-head CI."""
        wf = Path(".github/workflows/owner-comment-ci-dispatch.yml").read_text()
        self.assertIn(
            "group: ${{ startsWith(github.event.comment.body, '/ur-ci hp-research') "
            "&& 'owner-comment-hp-research' || "
            "format('owner-comment-dispatch-{0}', github.event.issue.number) }}", wf)
        self.assertIn("cancel-in-progress: false", wf)
        # The run-census check must remain inside the serialized job, not only
        # in a separate comment handler that could race across PR numbers.
        self.assertIn("python3 tools/ci_owner_comment_dispatch.py", wf)
        dispatcher = Path("tools/ci_owner_comment_dispatch.py").read_text()
        self.assertIn("recent_science_run(get_runs(SCIENCE_WORKFLOW, \"main\"), now)",
                      dispatcher)
        self.assertIn("if existing is None:\\n        dispatch(SCIENCE_WORKFLOW, \"main\")".replace("\\n", "\n"),
                      dispatcher)

    def test_only_default_branch_trusted_source_and_existing_dispatch_targets(self):
        wf = Path(".github/workflows/owner-comment-ci-dispatch.yml").read_text()
        self.assertIn("types: [created]", wf)
        self.assertIn("actions: write", wf)
        self.assertIn("github.event.comment.author_association == 'OWNER'", wf)
        self.assertIn("github.event.comment.user.login == github.repository_owner", wf)
        self.assertIn("persist-credentials: false", wf)
        for name in ("tooling-unit-tests.yml", "ghost-target-native-acceptance.yml"):
            self.assertIn("workflow_dispatch:",
                Path(".github/workflows", name).read_text())


if __name__ == "__main__":
    unittest.main()
