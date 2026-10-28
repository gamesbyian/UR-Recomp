"""ROM-free contract: one hosted Windows PE runs the complete MENU-10 witness.

The workflow-only opt-in never constitutes physical controller or release QA.
"""
from pathlib import Path
import unittest

WORKFLOW = (Path(__file__).resolve().parents[2] / ".github" / "workflows" /
            "modern-visual-native-win32-capture.yml")
BRANCH = "qa/menu10-full-cycle-same-pe-20261028"
STEPS = (
    "Observe default stock attract motion and wake in real final SDL",
    "Retain exact stock attract guest-to-final-SDL pixels and logs",
    "Observe genuine P1 Start exit and rapid source-main recovery",
    "Retain exact Windows rapid Start-exit source and SDL evidence",
    "Observe A-wake then distinct real P1 Start source exit",
    "Retain A-wake then real Start original-source and final SDL evidence",
    "Observe keyboard-only wake then distinct Return guest demo exit",
    "Retain keyboard-only original-source and final SDL evidence",
)


def verify(text):
    lines = text.splitlines()
    for label in STEPS:
        matches = [i for i, line in enumerate(lines)
                   if line.strip() == "- name: " + label]
        if len(matches) != 1:
            raise ValueError("missing or duplicate MENU-10 step: " + label)
        if not lines[matches[0] + 1].strip().startswith("if:"):
            raise ValueError("missing step guard: " + label)
        if "github.head_ref == '" + BRANCH + "'" not in lines[matches[0] + 1]:
            raise ValueError("same-source branch missing from step: " + label)
    jobs = [i for i, line in enumerate(lines) if line.strip() == "actual-sdl-root:"]
    if len(jobs) != 1 or not any(
            "github.head_ref == '" + BRANCH + "'" in line
            for line in lines[jobs[0] + 1:jobs[0] + 7]):
        raise ValueError("same-source branch missing from actual Windows job")
    if text.count("github.head_ref == '" + BRANCH + "'") != len(STEPS) + 1:
        raise ValueError("unexpected same-source branch scope")
    for name in (
        "menu10-stock-attract-native-win32-final-sdl",
        "menu10-real-p1-start-rapid-guest-exit",
        "menu10-post-wake-real-start-exit",
        "menu10-keyboard-post-wake-source-exit",
    ):
        if text.count("name: " + name) != 1:
            raise ValueError("missing/duplicate artifact: " + name)


class SamePeMenu10WorkflowTest(unittest.TestCase):
    def test_one_windows_job_uses_all_existing_routes_and_artifacts(self):
        verify(WORKFLOW.read_text(encoding="utf-8"))

    def test_missing_route_guard_fails_closed(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        target = "- name: Observe keyboard-only wake then distinct Return guest demo exit"
        pos = text.index(target)
        before, after = text[:pos], text[pos:]
        after = after.replace(" || github.head_ref == '" + BRANCH + "'", "", 1)
        with self.assertRaisesRegex(ValueError, "branch missing"):
            verify(before + after)

    def test_missing_upload_guard_fails_closed(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        target = "- name: Retain exact stock attract guest-to-final-SDL pixels and logs"
        pos = text.index(target)
        before, after = text[:pos], text[pos:]
        after = after.replace(" || github.head_ref == '" + BRANCH + "'", "", 1)
        with self.assertRaisesRegex(ValueError, "branch missing"):
            verify(before + after)


if __name__ == "__main__":
    unittest.main()
