"""Owner-only opt-in ONE-03 earned workflow dispatch contract (no network)."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from ci_owner_comment_dispatch import intent, process

REPO = "gamesbyian/UR-Recomp"
SHA = "a" * 40
COMMAND = "/ur-ci run modern-results-navigation-acceptance.yml " + SHA + " earned"


def event(body=COMMAND):
    return {"action": "created", "repository": {"full_name": REPO},
            "issue": {"number": 2813, "pull_request": {"url": "pr"}},
            "comment": {"body": body, "user": {"login": "gamesbyian"},
                        "author_association": "OWNER"}}


def pr(draft=True):
    return {"number": 2813, "state": "open", "draft": draft,
            "head": {"repo": {"full_name": REPO}, "sha": SHA,
                     "ref": "product/one03-source-earned-next-result-cold-reopen-20261028"}}


class OwnerEarnedDispatchTests(unittest.TestCase):
    def test_exact_draft_earned_command_dispatches_fixed_input(self):
        calls = []
        result = process(event(), REPO, "gamesbyian",
            lambda n: (calls.append(("pr", n)), pr())[1],
            lambda w, r: (calls.append(("census", w, r)),
                          {"total_count": 0, "workflow_runs": []})[1],
            lambda *args: calls.append(("dispatch", *args)))
        self.assertEqual(calls, [
            ("pr", 2813),
            ("census", "modern-results-navigation-acceptance.yml",
             "product/one03-source-earned-next-result-cold-reopen-20261028"),
            ("dispatch", "modern-results-navigation-acceptance.yml",
             "product/one03-source-earned-next-result-cold-reopen-20261028",
             {"results_shard": "earned"})])
        self.assertEqual(result[2], SHA)
        self.assertIsNone(result[4])

    def test_no_unrequested_native_mode_or_legacy_inputs(self):
        invalid = [
            "/ur-ci run modern-results-navigation-acceptance.yml " + SHA,
            "/ur-ci run modern-results-navigation-acceptance.yml " + SHA + " all",
            "/ur-ci run modern-results-navigation-acceptance.yml " + SHA + " earned extra",
            "/ur-ci run tooling-unit-tests.yml " + SHA + " earned",
            "/ur-ci run ghost-target-native-acceptance.yml " + SHA + " earned",
            "/ur-ci run modern-results-navigation-acceptance.yml b earned",
        ]
        for body in invalid:
            with self.subTest(body=body):
                self.assertIsNone(process(event(body), REPO, "gamesbyian",
                    lambda _: self.fail("invalid command queried PR"),
                    lambda *a: self.fail("invalid command queried runs"),
                    lambda *a: self.fail("invalid command dispatched")))

    def test_draft_only_and_exact_sha_fork_ref_guards(self):
        variants = [pr(draft=False)]
        for key, value in (("sha", "b" * 40), ("ref", "main"),
                           ("ref", "bad/../branch"),
                           ("repo", {"full_name": "other/repo"})):
            candidate = pr()
            candidate["head"][key] = value
            variants.append(candidate)
        for candidate in variants:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                process(event(), REPO, "gamesbyian", lambda _: candidate,
                    lambda *a: self.fail("invalid PR queried runs"),
                    lambda *a: self.fail("invalid PR dispatched"))

    def test_untrusted_author_rejected(self):
        for key, value in (("author_association", "COLLABORATOR"),
                           ("user", {"login": "other"})):
            e = event()
            e["comment"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                intent(e, REPO, "gamesbyian")

    def test_existing_earned_run_not_restarted(self):
        for status in ("queued", "in_progress", "waiting"):
            with self.subTest(status=status):
                result = process(event(), REPO, "gamesbyian", lambda _: pr(),
                    lambda w, r: {"total_count": 1, "workflow_runs": [{
                        "id": 1234, "event": "workflow_dispatch", "head_branch": r,
                        "head_sha": SHA, "status": status}]},
                    lambda *a: self.fail("duplicate earned dispatch"))
                self.assertEqual(result[4], 1234)

    def test_existing_ready_full_unit_command_unchanged(self):
        sent = []
        e = event("/ur-ci run tooling-unit-tests.yml " + SHA)
        result = process(e, REPO, "gamesbyian", lambda _: pr(draft=False),
            lambda w, r: {"total_count": 0, "workflow_runs": []},
            lambda *a: sent.append(a))
        self.assertEqual(sent, [("tooling-unit-tests.yml",
                                 "product/one03-source-earned-next-result-cold-reopen-20261028")])
        self.assertEqual(result[2], SHA)


if __name__ == "__main__":
    unittest.main()
