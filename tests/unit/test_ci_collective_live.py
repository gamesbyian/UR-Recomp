"""Read-only GitHub P1 candidate verification negative controls."""
import copy
import unittest

from tools.ci_collective_live import live_attest, REPO

A = "a" * 40
B = "b" * 40
C = "c" * 40
D = "d" * 40
ROOT = "/repos/" + REPO


def setup():
    manifest = {
        "schema": 1, "batch_id": "UR-CI-PILOT-001", "base_sha": A, "candidate_sha": B,
        "members": [
            {"work_id": "WIDE-07", "pr": 101, "head_sha": C,
             "changed_paths": ["native/a.cpp"]},
            {"work_id": "TITLE-08", "pr": 102, "head_sha": D,
             "changed_paths": ["native/b.cpp"]},
        ],
    }
    routes = {ROOT + "/branches/main": {"commit": {"sha": A}},
              ROOT + "/commits/" + B: {"sha": B}}
    for ancestor in (A, C, D):
        routes[ROOT + "/compare/" + ancestor + "..." + B] = {
            "status": "ahead", "behind_by": 0}
    for i, (number, head, path) in enumerate(((101, C, "native/a.cpp"),
                                               (102, D, "native/b.cpp"))):
        routes[ROOT + f"/pulls/{number}"] = {
            "number": number, "state": "open", "draft": False, "mergeable": True,
            "base": {"ref": "main", "repo": {"full_name": REPO}},
            "head": {"sha": head, "repo": {"full_name": REPO}}, "changed_files": 1}
        routes[ROOT + f"/pulls/{number}/files?per_page=100&page=1"] = [
            {"status": "modified", "filename": path, "sha": str(i + 1) * 40}]
        routes[ROOT + f"/contents/{path}?ref=" + B] = {
            "type": "file", "sha": str(i + 1) * 40}
    return manifest, routes


class Fake:
    def __init__(self, routes):
        self.routes = copy.deepcopy(routes)
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        return copy.deepcopy(self.routes.get(url))


class TestLiveAttestation(unittest.TestCase):
    def test_exact_source_and_blobs_are_positive_only(self):
        m, routes = setup()
        receipt = live_attest(m, Fake(routes))
        self.assertEqual(receipt["file_blob_matches"], 2)
        self.assertTrue(receipt["candidate_ancestry_and_member_files_checked"])
        self.assertFalse(receipt["complete_required_tests_executed"])
        self.assertFalse(receipt["personal_hp_pr_code_execution_authorized"])
        self.assertFalse(receipt["independent_writer_clearance"])

    def test_main_moved(self):
        m, routes = setup()
        routes[ROOT + "/branches/main"]["commit"]["sha"] = C
        with self.assertRaisesRegex(ValueError, "main moved"):
            live_attest(m, Fake(routes))

    def test_member_head_moved(self):
        m, routes = setup()
        routes[ROOT + "/pulls/102"]["head"]["sha"] = A
        with self.assertRaisesRegex(ValueError, "base/head changed"):
            live_attest(m, Fake(routes))

    def test_missing_file_page(self):
        m, routes = setup()
        routes.pop(ROOT + "/pulls/102/files?per_page=100&page=1")
        with self.assertRaisesRegex(ValueError, "malformed PR file page"):
            live_attest(m, Fake(routes))

    def test_incomplete_page(self):
        m, routes = setup()
        routes[ROOT + "/pulls/102"]["changed_files"] = 2
        with self.assertRaisesRegex(ValueError, "census incomplete"):
            live_attest(m, Fake(routes))

    def test_unclaimed_changed_file(self):
        m, routes = setup()
        routes[ROOT + "/pulls/102/files?per_page=100&page=1"][0]["filename"] = "native/other.cpp"
        routes[ROOT + "/contents/native/other.cpp?ref=" + B] = {
            "type": "file", "sha": "2" * 40}
        with self.assertRaisesRegex(ValueError, "paths mismatch"):
            live_attest(m, Fake(routes))

    def test_blob_overwritten_on_candidate_merge(self):
        m, routes = setup()
        routes[ROOT + "/contents/native/b.cpp?ref=" + B]["sha"] = "9" * 40
        with self.assertRaisesRegex(ValueError, "member file bytes"):
            live_attest(m, Fake(routes))

    def test_missing_candidate_file(self):
        m, routes = setup()
        routes.pop(ROOT + "/contents/native/a.cpp?ref=" + B)
        with self.assertRaisesRegex(ValueError, "missing or malformed candidate file"):
            live_attest(m, Fake(routes))

    def test_member_not_ancestor(self):
        m, routes = setup()
        routes[ROOT + "/compare/" + C + "..." + B]["behind_by"] = 1
        with self.assertRaisesRegex(ValueError, "not descendant"):
            live_attest(m, Fake(routes))

    def test_indeterminate_mergeability_is_not_a_pass(self):
        m, routes = setup()
        routes[ROOT + "/pulls/102"]["mergeable"] = None
        with self.assertRaisesRegex(ValueError, "not open, ready"):
            live_attest(m, Fake(routes))

    def test_draft_is_not_ready(self):
        m, routes = setup()
        routes[ROOT + "/pulls/101"]["draft"] = True
        with self.assertRaisesRegex(ValueError, "not open, ready"):
            live_attest(m, Fake(routes))

    def test_same_file_in_two_members_even_if_declared_otherwise(self):
        m, routes = setup()
        routes[ROOT + "/pulls/102/files?per_page=100&page=1"][0]["filename"] = "native/a.cpp"
        with self.assertRaisesRegex(ValueError, "collision"):
            live_attest(m, Fake(routes))

    def test_rename_source_must_be_removed(self):
        m, routes = setup()
        m["members"][0]["changed_paths"] = ["native/a.cpp", "native/old.cpp"]
        routes[ROOT + "/pulls/101/files?per_page=100&page=1"][0].update({
            "status": "renamed", "previous_filename": "native/old.cpp"})
        receipt = live_attest(m, Fake(routes))
        self.assertEqual(receipt["removed_paths_confirmed_absent"], 1)
        routes[ROOT + "/contents/native/old.cpp?ref=" + B] = {
            "type": "file", "sha": "f" * 40}
        with self.assertRaisesRegex(ValueError, "source path survived"):
            live_attest(m, Fake(routes))

    def test_actual_deletion_must_be_missing(self):
        m, routes = setup()
        routes[ROOT + "/pulls/101/files?per_page=100&page=1"][0]["status"] = "removed"
        routes.pop(ROOT + "/contents/native/a.cpp?ref=" + B)
        receipt = live_attest(m, Fake(routes))
        self.assertEqual(receipt["removed_paths_confirmed_absent"], 1)
        self.assertEqual(receipt["file_blob_matches"], 1)
        routes[ROOT + "/contents/native/a.cpp?ref=" + B] = {
            "type": "file", "sha": "1" * 40}
        with self.assertRaisesRegex(ValueError, "source path survived"):
            live_attest(m, Fake(routes))

    def test_changed_main_during_validation(self):
        m, routes = setup()

        class Moving(Fake):
            def __call__(self, url):
                if url == ROOT + "/branches/main" and url in self.calls:
                    return {"commit": {"sha": C}}
                return super().__call__(url)

        with self.assertRaisesRegex(ValueError, "main moved during"):
            live_attest(m, Moving(routes))

    def test_stale_pr_at_final_read(self):
        m, routes = setup()

        class Moving(Fake):
            def __call__(self, url):
                if url == ROOT + "/pulls/101" and url in self.calls:
                    current = super().__call__(url)
                    current["head"]["sha"] = A
                    return current
                return super().__call__(url)

        with self.assertRaisesRegex(ValueError, "changed during inspection"):
            live_attest(m, Moving(routes))

    def test_unauthorized_repository_rejected(self):
        m, routes = setup()
        with self.assertRaisesRegex(ValueError, "allowlist"):
            live_attest(m, Fake(routes), repo="other/repo")


if __name__ == "__main__":
    unittest.main()
