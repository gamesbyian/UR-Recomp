"""Real data-bound authorization and no-dispatch regressions (no GitHub writes)."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from ci_owner_comment_dispatch import intent, exact_head, process

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
                    lambda w, ref: calls.append(("dispatch", w, ref)))
                self.assertEqual(calls, [("get", 2837), ("dispatch", name, "ops/test-ref")])
                self.assertEqual(outcome[2], SHA)

    def test_noncommands_and_edited_or_nonpr_comments_never_hit_api(self):
        for body in ("just a normal comment", "/ur-ci run arbitrary.yml " + SHA,
                     "/ur-ci run tooling-unit-tests.yml b",
                     "/ur-ci run tooling-unit-tests.yml " + SHA + " extra"):
            self.assertIsNone(process(event(text=body), REPO, "gamesbyian",
                lambda _: self.fail("queried PR on noncommand"),
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
                    lambda _: p, lambda *args: self.fail("dispatched invalid PR"))
        for field, value in (("state", "closed"), ("draft", True)):
            p = pr()
            p[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                exact_head(p, 2837, REPO, SHA)

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
