from pathlib import Path
import re
import unittest


WORKFLOWS = Path(".github/workflows")
MAIN_PUSH_ALLOWLIST = set()

DORMANT_MANUAL_ONLY = {
    "smv-tools.yml",
    "racer-composition-mesen.yml",
    "racer-asset-exact-roundtrip.yml",
    "racer-hd-replacement-prototype.yml",
    "object-activation-probe.yml",
    "offline-core-smoke.yml",
    "challenge-writer-entry-scan.yml",
    "analyze-reference-roms.yml",
    "audio-startup-cross-core.yml",
    "bottom-edge-cross-core.yml",
    "cc65-da65-closure-eval.yml",
    "challenge-award-aot-probe.yml",
    "course-byte11-exact-writer.yml",
    "course-header-cadence.yml",
    "course-layout-plane-probe.yml",
    "course-presentation-contract-sample.yml",
    "course-presentation-contract.yml",
    "course-runtime-payload.yml",
    "course-stream-pointer-search.yml",
    "generated-challenge-seam-probe.yml",
    "historical-smv-first-race.yml",
    "historical-snes9x151-medal.yml",
    "historical-wip-dragster.yml",
    "independent-reference-route.yml",
    "medal-progression-search.yml",
    "mesence-two-player-reference.yml",
    "object-liveness-dragster.yml",
    "preparation-emission-probe.yml",
    "qualification-generation-ref-scan.yml",
    "quick-practice-track-selection.yml",
    "race-behavior-differential.yml",
    "race-collision-differential.yml",
    "race-finish-differential.yml",
    "race-landing-differential.yml",
    "race-rotation-differential.yml",
    "rnc-writer-decoder-probe.yml",
    "rnc-writer-static-classification.yml",
    "s2-desktop-digest-reference.yml",
    "snes9x-island-closure.yml",
    "snesrecomp-c2-network-audit.yml",
    "snesref-input-route.yml",
    "sram-mapping-probe.yml",
    "switch-s0-compile-probe.yml",
    "switch-s1-runtime-shell.yml",
    "switch-s2-executable-link.yml",
    "switch-s2-guest-aot.yml",
    "switch-s2-init-execution.yml",
    "switch-s2-link-surface.yml",
    "switch-s2-runtime-core.yml",
    "switch-shared-core-portability.yml",
    "targeted-wram-store-scan.yml",
    "tcrf-boot-vram.yml",
    "tcrf-unused-content-reconcile.yml",
    "title-transition-cross-core.yml",
    "trace-course-buffer-writers.yml",
    "trace-race-wram-writers.yml",
    "two-player-reference.yml",
    "vs-split-screen-reference.yml",
    "widescreen-composition-matrix.yml",
    "widescreen-native-hook.yml",
    "widescreen-plus8-oam-probe.yml",
    "widescreen-strip-scheduling-plus8.yml",
    "widescreen-tiny-margin-probe.yml",
    "widescreen-vs-plus16-capacity.yml",
    "widescreen-vs-plus24-capacity.yml",
    "widescreen-vs-plus32-capacity.yml",
    "widescreen-vs-plus40-capacity.yml",
    "widescreen-vs-plus48-capacity.yml",
    "widescreen-vs-policy.yml",
    "widescreen-vs-preparation-trace.yml",
    "window-xor-recon.yml",
}


def _block(text: str, key: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(key)}:\s*\n(.*?)(?=^  [A-Za-z_][A-Za-z0-9_-]*:\s*$|^[A-Za-z_][A-Za-z0-9_-]*:\s*$|\Z)",
        text,
    )
    return match.group(1) if match else ""


def _pushes_main(text: str) -> bool:
    push = _block(text, "push")
    if not push:
        return False
    return bool(
        re.search(r"(?m)^      - main\s*$", push)
        or re.search(r"(?m)^    branches:\s*\[\s*main\s*\]\s*$", push)
    )


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

    def test_pull_requests_are_path_scoped(self):
        offenders = []
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text()
            pull_request = _block(text, "pull_request")
            if pull_request and "    paths:\n" not in pull_request:
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            f"automatic pull requests must be path-scoped: {offenders}",
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

    def test_coordination_docs_never_trigger_automatic_ci(self):
        forbidden = {
            "docs/WORK-QUEUE.md",
            "docs/PROJECT-PLAN.md",
            "docs/SEMANTIC-SUFFICIENCY.md",
        }
        offenders = []
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text()
            pull_request = _block(text, "pull_request")
            push = _block(text, "push")
            automatic_paths = "\n".join((pull_request, push))
            matched = sorted(item for item in forbidden if item in automatic_paths)
            if matched:
                offenders.append((path.name, matched))
        self.assertEqual(
            offenders,
            [],
            "coordination/planning docs are not executable inputs and must not "
            f"fan out CI when agents update them: {offenders}",
        )

    def test_deferred_switch_shared_core_is_manual_only(self):
        path = WORKFLOWS / "switch-shared-core-portability.yml"
        text = path.read_text()
        self.assertIn("  workflow_dispatch:", text)
        self.assertFalse(
            _block(text, "pull_request"),
            "Switch is deferred while Windows x64 is primary; shared-core "
            "portability must be explicitly dispatched rather than triggered "
            "by every native/product or native/title edit",
        )

    def test_dormant_research_is_manual_only(self):
        offenders = []
        for name in sorted(DORMANT_MANUAL_ONLY):
            path = WORKFLOWS / name
            text = path.read_text()
            if _block(text, "pull_request") or _block(text, "push"):
                offenders.append(name)
            self.assertIn("  workflow_dispatch:", text, name)
        self.assertEqual(
            offenders,
            [],
            f"retained research/deferred-platform workflows must be manually dispatched: {offenders}",
        )

    def test_windows_smoke_runs_only_on_final_main(self):
        text = (WORKFLOWS / "windows-native-smoke.yml").read_text()
        self.assertTrue(_pushes_main(text))
        self.assertFalse(_block(text, "pull_request"))

    def test_native_ui_evidence_does_not_rebuild_per_shard(self):
        text = (WORKFLOWS / "native-ui-evidence.yml").read_text()
        self.assertNotIn("matrix.shard", text)
        self.assertNotIn('"native/product/**"', text)


    def test_onboarding_acceptance_does_not_trigger_on_docs_only(self):
        text = (WORKFLOWS / "modern-onboarding-practice-acceptance.yml").read_text()
        self.assertNotIn('"docs/MODERN-PRODUCT-LAYER.md"', _block(text, "pull_request"))


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
