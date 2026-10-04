from pathlib import Path
import re
import unittest


WORKFLOWS = Path(".github/workflows")
MAIN_PUSH_ALLOWLIST = {
    "historical-smv-first-race.yml",
    "historical-wip-dragster.yml",
}


def _block(text: str, key: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(key)}:\s*\n(.*?)(?=^  [A-Za-z_][A-Za-z0-9_-]*:\s*$|^[A-Za-z_][A-Za-z0-9_-]*:\s*$|\Z)",
        text,
    )
    return match.group(1) if match else ""


def _pushes_main(text: str) -> bool:
    push = _block(text, "push")
    return bool(push and re.search(r"(?m)^      - main\s*$", push))


class CiTriggerPolicyTest(unittest.TestCase):
    def test_pr_validation_is_not_repeated_after_merge(self):
        offenders = []
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text()
            has_pr = bool(_block(text, "pull_request"))
            if has_pr and _pushes_main(text) and path.name not in MAIN_PUSH_ALLOWLIST:
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            "pure validation workflows must not run both on pull_request and "
            "again after merge to main; keep main push only for explicit "
            f"post-merge side effects. offenders={offenders}",
        )

    def test_main_pushes_are_path_scoped(self):
        offenders = []
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text()
            push = _block(text, "push")
            if _pushes_main(text) and "    paths:\n" not in push:
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            f"automatic main pushes must be path-scoped: {offenders}",
        )

    def test_automatic_workflows_declare_concurrency(self):
        offenders = []
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text()
            automatic = bool(_block(text, "pull_request")) or _pushes_main(text)
            if automatic and not re.search(r"(?m)^concurrency:\s*$", text):
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            f"automatic workflows must cancel or serialize by ref: {offenders}",
        )

    def test_main_push_allowlist_is_evidence_writing(self):
        for name in MAIN_PUSH_ALLOWLIST:
            path = WORKFLOWS / name
            text = path.read_text()
            self.assertTrue(_block(text, "pull_request"), name)
            self.assertTrue(_pushes_main(text), name)
            self.assertRegex(text, r"(?ms)^permissions:\s*\n(?:.*\n)*?  contents: write\s*$")
            self.assertTrue(
                "cancel-in-progress: false" in text
                or "cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}" in text,
                name,
            )


if __name__ == "__main__":
    unittest.main()
