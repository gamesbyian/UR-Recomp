from pathlib import Path
import re
import unittest


WORKFLOWS = Path(".github/workflows")
MAIN_PUSH_ALLOWLIST = set()

ABSOLUTE_FRAME_AUTOMATIC_ALLOWLIST = {
    "native-build-smoke.yml",
    "native-ui-evidence.yml",
    "racer-native-presentation-acceptance.yml",
}

DESKTOP_UI_DRIVER_AUTOMATIC_ALLOWLIST = {
    "native-ui-evidence.yml",
    "modern-shared-native-acceptance.yml",
}

EXPENSIVE_PR_WORKFLOWS = {
    "modern-shared-native-acceptance.yml",
    "completed-run-replay-acceptance.yml",
    "modern-onboarding-practice-acceptance.yml",
    "modern-race-restart-acceptance.yml",
    "modern-results-navigation-acceptance.yml",
    "multiplayer-match-capture-acceptance.yml",
    "native-build-smoke.yml",
    "native-ui-evidence.yml",
    "racer-native-presentation-acceptance.yml",
    "widescreen-4x3-regression.yml",
}

DORMANT_MANUAL_ONLY = {
    "regional-retail-static-analysis.yml",
    "regional-retail-frontend-comparison.yml",
    "regional-retail-course-payloads.yml",
    "regional-retail-audio-packages.yml",
    "racer-staging-consumers.yml",
    "racer-piece-semantics.yml",
    "racer-piece-render-binding.yml",
    "racer-packed-low2.yml",
    "racer-asset-roundtrip.yml",
    "dual-player-input.yml",
    "deterministic-differential.yml",
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


def _workflow_paths() -> list[Path]:
    return sorted({*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")})


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
        for path in _workflow_paths():
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
        for path in _workflow_paths():
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
        for path in _workflow_paths():
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
        for path in _workflow_paths():
            text = path.read_text()
            automatic = bool(_block(text, "pull_request")) or _pushes_main(text)
            if automatic and not re.search(r"(?m)^concurrency:\s*$", text):
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            f"automatic workflows must cancel or serialize by ref: {offenders}",
        )

    def test_expensive_pr_gates_defer_drafts_and_run_when_ready(self):
        offenders = []
        required_if = (
            "if: github.event_name != 'pull_request' || "
            "github.event.pull_request.draft == false"
        )
        for name in sorted(EXPENSIVE_PR_WORKFLOWS):
            text = (WORKFLOWS / name).read_text()
            pull_request = _block(text, "pull_request")
            jobs = text.split("\njobs:", 1)[1] if "\njobs:" in text else ""
            first_job = re.search(
                r"(?ms)^  [A-Za-z0-9_-]+:\s*\n(.*?)(?=^  [A-Za-z0-9_-]+:\s*$|\Z)",
                jobs,
            )
            header = (
                first_job.group(1).split("    steps:", 1)[0]
                if first_job
                else ""
            )
            problems = []
            if "ready_for_review" not in pull_request:
                problems.append("missing ready_for_review trigger")
            if required_if not in header:
                problems.append("first job does not skip draft PRs")
            if problems:
                offenders.append((name, problems))
        self.assertEqual(
            offenders,
            [],
            "expensive PR gates must stay cheap while a PR is draft and run once "
            f"it becomes review-ready: {offenders}",
        )

    def test_native_build_gates_do_not_redownload_runner_tooling(self):
        forbidden = {"cmake", "ninja-build", "libsdl2-dev"}
        offenders = []
        for name in sorted(EXPENSIVE_PR_WORKFLOWS):
            lines = (WORKFLOWS / name).read_text().splitlines()
            for index, line in enumerate(lines):
                if "apt-get" not in line or "install" not in line:
                    continue
                block = [line]
                cursor = index + 1
                while block[-1].rstrip().endswith("\\") and cursor < len(lines):
                    block.append(lines[cursor])
                    cursor += 1
                joined = " ".join(block)
                matched = sorted(item for item in forbidden if item in joined)
                if matched:
                    offenders.append((name, index + 1, matched))
        self.assertEqual(
            offenders,
            [],
            "Ubuntu-hosted native gates must use runner-provided CMake/Ninja and "
            f"the canonical SDL3 source rather than redownloading old tooling: {offenders}",
        )

    def test_shared_modern_native_acceptance_builds_once_and_fans_out(self):
        text = (WORKFLOWS / "modern-shared-native-acceptance.yml").read_text()
        self.assertIn("  build:", text)
        self.assertIn("  ghost-target:", text)
        self.assertIn("  profile-panel:", text)
        self.assertEqual(text.count("Build shared Modern native candidate"), 1)
        self.assertIn("shared-modern-native-candidate", text)
        consumers = text.split("  ghost-target:", 1)[1]
        self.assertNotIn("cmake --build", consumers)
        self.assertNotIn("libgl1-mesa-dev", consumers)
        self.assertIn("xvfb", consumers)
        self.assertIn("xdotool", consumers)

    def test_superseded_profile_gates_are_manual_only(self):
        for name in (
            "ghost-target-native-acceptance.yml",
            "profile-panel-native-acceptance.yml",
        ):
            text = (WORKFLOWS / name).read_text()
            self.assertIn("  workflow_dispatch:", text)
            self.assertFalse(_block(text, "pull_request"))

    def test_native_ui_capture_installs_runtime_only_dependencies(self):
        text = (WORKFLOWS / "native-ui-evidence.yml").read_text()
        capture = text.split("  capture:", 1)[1].split("  aggregate:", 1)[0]
        install = capture.split(
            "- name: Install native UI runtime dependencies", 1
        )[1].split("- name:", 1)[0]
        self.assertIn("xvfb xdotool", install)
        self.assertNotIn("-dev", install)
        self.assertNotIn("cmake", install)
        self.assertNotIn("ninja", install)

    def test_coordination_docs_never_trigger_automatic_ci(self):
        forbidden = {
            "docs/WORK-QUEUE.md",
            "docs/PROJECT-PLAN.md",
            "docs/SEMANTIC-SUFFICIENCY.md",
        }
        offenders = []
        for path in _workflow_paths():
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

    def test_native_ui_evidence_scope_is_bounded(self):
        text = (WORKFLOWS / "native-ui-evidence.yml").read_text()
        self.assertNotIn('"native/product/**"', text)
        self.assertIn("fail-fast: false", text)
        match = re.search(r"shard:\s*\[([^\]]+)\]", text)
        self.assertIsNotNone(match)
        shards = [item.strip() for item in match.group(1).split(",")]
        self.assertLessEqual(len(shards), 5)


    def test_onboarding_acceptance_does_not_trigger_on_docs_only(self):
        text = (WORKFLOWS / "modern-onboarding-practice-acceptance.yml").read_text()
        self.assertNotIn('"docs/MODERN-PRODUCT-LAYER.md"', _block(text, "pull_request"))


    def test_onboarding_uses_one_candidate_with_bounded_fanout(self):
        text = (WORKFLOWS / "modern-onboarding-practice-acceptance.yml").read_text()
        self.assertIn("  build:", text)
        self.assertIn("modern-onboarding-native-candidate", text)
        self.assertIn("  core-acceptance:", text)
        self.assertIn("  independent-acceptance:", text)
        match = re.search(r"shard:\s*\[([^\]]+)\]", text)
        self.assertIsNotNone(match)
        shards = [item.strip() for item in match.group(1).split(",")]
        self.assertLessEqual(len(shards), 3)
        consumer = text.split("  core-acceptance:", 1)[1]
        self.assertIn("Install native runtime dependencies", consumer)
        runtime_install = consumer.split(
            "- name: Install native runtime dependencies", 1
        )[1].split("- name:", 1)[0]
        self.assertIn("xvfb xdotool", runtime_install)
        self.assertNotIn("-dev", runtime_install)
        self.assertNotIn("cmake", runtime_install)
        self.assertNotIn("ninja", runtime_install)


    def test_local_multiplayer_contract_does_not_trigger_on_docs_only(self):
        text = (WORKFLOWS / "local-multiplayer-product-contracts.yml").read_text()
        self.assertNotIn('"docs/LOCAL-MULTIPLAYER-SETUP.md"', _block(text, "pull_request"))


    def test_native_build_smoke_stays_fast_and_bounded(self):
        text = (WORKFLOWS / "native-build-smoke.yml").read_text()
        self.assertIn("    timeout-minutes: 15", text)
        for required in (
            "Native boot smoke",
            "Deterministic native input route",
            "Shipping Widescreen composition acceptance",
        ):
            self.assertIn(required, text)
        for delegated in (
            "Modern Tour Resume Restart acceptance",
            "Modern racer profile panel acceptance",
            "Modern ghost target profile persistence acceptance",
            "Shipping Widescreen stock-parity acceptance",
            "Modern pause-settings row persistence acceptance",
            "Modern Exit to Frontend acceptance",
        ):
            self.assertNotIn(
                delegated,
                text,
                f"{delegated} is a focused feature journey and must not regrow the fast smoke gate",
            )


    def test_workflow_dispatch_has_a_yaml_boundary(self):
        offenders = []
        bad = re.compile(r"workflow_dispatch:(?:jobs:|permissions:|concurrency:|env:)")
        for path in _workflow_paths():
            if bad.search(path.read_text()):
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            f"workflow_dispatch must be separated from the next top-level key: {offenders}",
        )


    def test_automatic_jobs_have_timeouts(self):
        offenders = []
        for path in _workflow_paths():
            text = path.read_text()
            automatic = bool(_block(text, "pull_request")) or _pushes_main(text)
            if not automatic:
                continue
            runs_on = len(re.findall(r"(?m)^    runs-on:", text))
            timeouts = len(re.findall(r"(?m)^    timeout-minutes:", text))
            if timeouts < runs_on:
                offenders.append((path.name, runs_on, timeouts))
        self.assertEqual(
            offenders,
            [],
            f"automatic jobs that can hang must declare job-level timeouts: {offenders}",
        )

    def test_git_writers_serialize_without_cancellation(self):
        offenders = []
        for path in _workflow_paths():
            text = path.read_text()
            if not re.search(r"(?m)^\s*git push(?:\s|$)", text):
                continue
            serialized = (
                "cancel-in-progress: false" in text
                or "cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}" in text
            )
            if "  contents: write" not in text or not serialized:
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            "workflows that push generated evidence must serialize and must not "
            f"cancel an in-flight writer: {offenders}",
        )

    def test_automatic_specialists_do_not_follow_global_toolchain_registry(self):
        offenders = []
        for path in _workflow_paths():
            if path.name == "toolchain-bootstrap.yml":
                continue
            text = path.read_text()
            automatic = bool(_block(text, "pull_request")) or _pushes_main(text)
            if not automatic:
                continue
            triggers = "\n".join((_block(text, "pull_request"), _block(text, "push")))
            if '"tools/toolchain.json"' in triggers:
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            f"specialist automatic workflows must watch per-tool entries, not tools/toolchain.json: {offenders}",
        )

    def test_automatic_workflows_do_not_watch_all_tool_entries(self):
        offenders = []
        for path in _workflow_paths():
            if path.name == "toolchain-bootstrap.yml":
                continue
            text = path.read_text()
            automatic = bool(_block(text, "pull_request")) or _pushes_main(text)
            if not automatic:
                continue
            triggers = "\n".join((_block(text, "pull_request"), _block(text, "push")))
            if '"tools/toolchain-entries/**"' in triggers:
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            f"automatic workflows must name the toolchain entries they consume: {offenders}",
        )

    def test_staged_tool_inputs_are_declared_as_triggers(self):
        offenders = []
        for path in _workflow_paths():
            if path.name == "toolchain-bootstrap.yml":
                continue
            text = path.read_text()
            automatic = bool(_block(text, "pull_request")) or _pushes_main(text)
            if not automatic:
                continue
            jobs = text.split("\njobs:", 1)[1] if "\njobs:" in text else ""
            triggers = "\n".join((_block(text, "pull_request"), _block(text, "push")))
            required = []
            if "bootstrap_toolchain.py" in jobs:
                required.append("tools/bootstrap_toolchain.py")
            for tool in sorted(set(re.findall(r"--tool\s+([A-Za-z0-9_-]+)", jobs))):
                required.append(f"tools/toolchain-entries/{tool}.json")
            missing = [item for item in required if f'"{item}"' not in triggers]
            if missing:
                offenders.append((path.name, missing))
        self.assertEqual(
            offenders,
            [],
            "automatic workflows must declare the bootstrapper and exact staged "
            f"tool entries they consume: {offenders}",
        )

    def test_toolchain_contract_watches_patch_bytes(self):
        text = (WORKFLOWS / "toolchain-bootstrap.yml").read_text()
        self.assertIn('"tools/patches/**"', _block(text, "pull_request"))

    def test_main_push_does_not_self_trigger_on_workflow_yaml(self):
        offenders = []
        for path in _workflow_paths():
            text = path.read_text()
            push = _block(text, "push")
            own_path = f'.github/workflows/{path.name}'
            if _pushes_main(text) and own_path in push:
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            f"main-push workflows must not rerun solely because their own YAML changed: {offenders}",
        )

    def test_shell_continuations_are_not_interrupted_by_comments(self):
        offenders = []
        for path in _workflow_paths():
            lines = path.read_text().splitlines()
            for index, line in enumerate(lines[:-1]):
                if line.rstrip().endswith("\\") and lines[index + 1].lstrip().startswith("#"):
                    offenders.append(f"{path.name}:{index + 1}")
        self.assertEqual(
            offenders,
            [],
            "a comment after a backslash-continued shell line terminates or mutates "
            f"the command; move comments before the command: {offenders}",
        )

    def test_host_state_log_checks_do_not_depend_on_field_order(self):
        offenders = []
        assignment = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
        for path in _workflow_paths():
            for index, line in enumerate(path.read_text().splitlines(), start=1):
                if "grep" not in line or "UR_HOST_STATE LOADED" not in line:
                    continue
                if len(assignment.findall(line)) > 1:
                    offenders.append(f"{path.name}:{index}")
        self.assertEqual(
            offenders,
            [],
            "UR_HOST_STATE diagnostics are extensible key/value records; assert owned "
            f"fields independently rather than depending on field order: {offenders}",
        )

    def test_native_ui_builds_one_candidate_for_all_capture_shards(self):
        text = (WORKFLOWS / "native-ui-evidence.yml").read_text()
        build = text.split("  build:", 1)[1].split("  capture:", 1)[0]
        capture = text.split("  capture:", 1)[1].split("  aggregate:", 1)[0]
        self.assertEqual(build.count("cmake --build"), 1)
        self.assertIn("setup_project.sh", build)
        self.assertNotIn("cmake --build", capture)
        self.assertNotIn("setup_project.sh", capture)
        self.assertIn("name: build-ui-candidate", build)
        self.assertIn("name: native-ui-build-candidate", build)
        self.assertIn("needs: build", capture)
        aggregate = text.split("  aggregate:", 1)[1]
        self.assertNotIn("if: always()", aggregate.split("    steps:", 1)[0])
        self.assertIn("needs: [build, capture]", aggregate)

    def test_absolute_frame_coupling_does_not_spread(self):
        offenders = []
        frame_pattern = re.compile(
            r"(?:SNESRECOMP_SCREENSHOT_FRAME=\d+|\bframe=\d+)"
        )
        for path in _workflow_paths():
            text = path.read_text()
            automatic = bool(_block(text, "pull_request")) or _pushes_main(text)
            if not automatic or path.name in ABSOLUTE_FRAME_AUTOMATIC_ALLOWLIST:
                continue
            if frame_pattern.search(text):
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            "absolute-frame assertions are audited semantic debt and must not "
            f"spread to new automatic workflows: {offenders}",
        )

    def test_desktop_cursor_driving_does_not_spread(self):
        offenders = []
        driver = re.compile(r"\bxdotool\s+(?:key|search|windowfocus|windowactivate)\b")
        for path in _workflow_paths():
            text = path.read_text()
            automatic = bool(_block(text, "pull_request")) or _pushes_main(text)
            if not automatic or path.name in DESKTOP_UI_DRIVER_AUTOMATIC_ALLOWLIST:
                continue
            if driver.search(text):
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            "cursor-count desktop UI automation is audited debt; add a semantic "
            f"harness instead of spreading xdotool navigation: {offenders}",
        )

    def test_full_toolchain_build_matrix_is_manual_only(self):
        text = (WORKFLOWS / "toolchain-bootstrap.yml").read_text()
        self.assertRegex(
            text,
            r"(?m)^  build-smoke:\n    if: github\.event_name == 'workflow_dispatch'$",
        )

    def test_replay_acceptance_does_not_follow_generic_host_edits(self):
        text = (WORKFLOWS / "completed-run-replay-acceptance.yml").read_text()
        self.assertNotIn('"native/product/uniracers_modern_host.*"', _block(text, "pull_request"))


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
