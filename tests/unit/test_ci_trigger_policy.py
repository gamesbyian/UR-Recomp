from pathlib import Path
import re
import unittest


WORKFLOWS = Path(".github/workflows")
# The Windows producer runs on main product changes, and on PRs only when
# its own workflow is edited. These are disjoint invalidation surfaces.
MAIN_PUSH_ALLOWLIST = {"windows-native-smoke.yml"}

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
    "baldosa-windows-native-bridge.yml",
    "modern-native-heavy-router.yml",
    "modern-race-restart-acceptance.yml",
    "native-build-smoke.yml",
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

    def test_changed_workflow_actionlint_is_required_not_advisory(self):
        hygiene = (WORKFLOWS / "repo-hygiene.yml").read_text(encoding="utf-8")
        block = hygiene.split("      - name: Validate changed workflow files with actionlint", 1)[1]
        block = block.split("      - name: Advisory offline zizmor", 1)[0]
        self.assertNotIn("continue-on-error:", block)
        self.assertIn("gh api --paginate", block)
        self.assertIn("sha256sum --check --status", block)
        self.assertIn('actionlint" -oneline "${changed[@]}"', block)

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

    def test_baldosa_windows_draft_gate_keeps_opt_in_and_full_review_execution(self):
        workflow = (WORKFLOWS / "baldosa-windows-native-bridge.yml").read_text()
        pr = _block(workflow, "pull_request")
        self.assertIn("ready_for_review", pr)
        self.assertIn("converted_to_draft", pr)
        self.assertIn("synchronize", pr)
        self.assertIn("  workflow_dispatch:", workflow)
        self.assertIn("  workflow_call:", workflow)
        self.assertIn("      run_on_draft:", workflow)
        self.assertIn("        default: true", workflow.split("      run_on_draft:", 1)[1].split("\n\n", 1)[0])
        main_job = workflow.split("\njobs:\n", 1)[1]
        header = main_job.split("    steps:\n", 1)[0]
        self.assertIn(
            "if: github.event_name != 'pull_request' || "
            "github.event.pull_request.draft == false",
            header,
        )
        self.assertIn("|| inputs.run_on_draft == true", header)
        self.assertIn("runs-on: windows-2022", header)
        self.assertIn("timeout-minutes: 35", header)
        # Cancelling superseded PR jobs stays enabled and manual calls do
        # not cancel one another. The expensive Windows journey is still
        # present and reachable for non-draft PRs and dispatched branches.
        self.assertIn("cancel-in-progress: " + "$" +
                      "{{ github.event_name == 'pull_request' }}", workflow)
        self.assertIn("Build real native AOT Windows x64 title plus UR host bridges",
                      main_job)
        self.assertIn("Pilot parallel authentic Windows journeys", main_job)
        self.assertIn("Prove extracted CMD launcher", main_job)

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

    def test_modern_native_router_builds_once_and_calls_migrated_suites(self):
        text = (WORKFLOWS / "modern-native-heavy-router.yml").read_text()
        self.assertIn("  classify:", text)
        self.assertIn("  build:", text)
        self.assertEqual(text.count("Build canonical Modern native candidate"), 1)
        self.assertEqual(text.count("cmake --build"), 1)
        self.assertIn("modern-native-canonical-candidate", text)
        self.assertIn(
            "uses: ./.github/workflows/modern-shared-native-acceptance.yml",
            text,
        )
        self.assertIn(
            "uses: ./.github/workflows/modern-onboarding-practice-acceptance.yml",
            text,
        )
        self.assertIn(
            "uses: ./.github/workflows/native-ui-evidence.yml",
            text,
        )
        # Shared compilation is justified for any two selected suites.
        # A single suite keeps its own build, avoiding needless upload hops.
        for pair in (
            ("shared", "onboarding"),
            ("shared", "ui"),
            ("onboarding", "ui"),
        ):
            self.assertIn(
                f"needs.classify.outputs.{pair[0]} == 'true' && needs.classify.outputs.{pair[1]} == 'true'",
                text,
            )
        self.assertEqual(
            text.count("canonical_candidate: ${{ needs.build.result == 'success' }}"),
            3,
        )
        self.assertEqual(
            text.count("needs.build.result == 'success' || needs.build.result == 'skipped'"),
            3,
        )

        for name in (
            "modern-shared-native-acceptance.yml",
            "modern-onboarding-practice-acceptance.yml",
            "native-ui-evidence.yml",
        ):
            suite = (WORKFLOWS / name).read_text()
            self.assertIn("  workflow_call:", suite)
            self.assertFalse(_block(suite, "pull_request"))
            self.assertIn("canonical_candidate", suite)

    def test_manual_modern_campaign_preserves_pr_router_and_acceptance_boundary(self):
        text = (WORKFLOWS / "modern-native-heavy-router.yml").read_text()
        self.assertIn("  workflow_dispatch:", text)
        self.assertIn("if: github.event_name == 'pull_request'", text)
        self.assertIn("if: github.event_name == 'workflow_dispatch'", text)
        self.assertIn("cancel-in-progress: ${{ github.event_name == 'pull_request' }}", text)
        self.assertIn("Select established suite cohort for manual campaign", text)
        self.assertIn("uses: ./.github/workflows/windows-native-smoke.yml", text)
        self.assertIn("if: github.event_name == 'workflow_dispatch' && inputs.include_windows == true", text)
        self.assertIn("  campaign-report:", text)
        self.assertIn("tools/qa_modern_batch_campaign.py", text)
        # The manual cohort uses the existing canonical build, not three new ones.
        self.assertEqual(text.count("cmake --build"), 1)
        self.assertEqual(text.count("modern-native-canonical-candidate"), 1)

    def test_shared_modern_native_acceptance_builds_once_and_fans_out(self):
        text = (WORKFLOWS / "modern-shared-native-acceptance.yml").read_text()
        self.assertIn("  build:", text)
        self.assertIn("  ghost-target:", text)
        self.assertIn("  profile-panel:", text)
        self.assertIn("  results-navigation:", text)
        self.assertIn("  ordinary-2p:", text)
        self.assertIn("  completed-run-replay:", text)
        self.assertEqual(text.count("Build shared Modern native candidate"), 1)
        self.assertIn("shared-modern-native-candidate", text)
        consumers = text.split("  ghost-target:", 1)[1]
        self.assertNotIn("cmake --build", consumers)
        self.assertNotIn("libgl1-mesa-dev", consumers)
        self.assertIn("xvfb", consumers)
        self.assertIn("xdotool", consumers)

    def test_research_producers_reuse_shared_build_without_product_fanout(self):
        shared = (WORKFLOWS / "modern-shared-native-acceptance.yml").read_text()
        self.assertIn("      candidate_only:", shared)
        consumers = shared.split("  ghost-target:", 1)[1]
        # Every acceptance consumer is skipped for research; the build is not.
        self.assertEqual(consumers.count("if: ${{ inputs.candidate_only != true }}"), 5)
        self.assertNotIn("candidate_only", shared.split("  ghost-target:", 1)[0].split("jobs:", 1)[1])
        for name in ("qa-adaptive-frontier.yml", "qa-cumulative-native-metrics.yml",
                     "qa02-native-2p-seeded-endurance.yml"):
            self.assertIn("candidate_only: true", (WORKFLOWS / name).read_text(), name)
        # Product routers keep the full acceptance fan-out.
        self.assertNotIn("candidate_only", (WORKFLOWS / "modern-native-heavy-router.yml").read_text())

    def test_superseded_shared_candidate_gates_are_manual_only(self):
        for name in (
            "ghost-target-native-acceptance.yml",
            "profile-panel-native-acceptance.yml",
            "modern-results-navigation-acceptance.yml",
            "multiplayer-match-capture-acceptance.yml",
            "completed-run-replay-acceptance.yml",
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

    def test_release_ledger_mutations_run_existing_structural_validator(self):
        # Ledger evidence_refs are machine-adjudicated contracts; a docs-only
        # PR must not bypass the unit suite that rejects unsafe source paths.
        workflow = (WORKFLOWS / "tooling-unit-tests.yml").read_text()
        self.assertIn('"docs/RELEASE-QUALITY-LEDGER.json"',
                      _block(workflow, "pull_request"))

    def test_romless_archive_auditor_invalidates_real_windows_gate(self):
        # The ZIP inspector runs in the same native Windows packaging job;
        # changing only its source or tests must not bypass that job.
        workflow = (WORKFLOWS / "baldosa-windows-native-bridge.yml").read_text()
        routed = _block(workflow, "pull_request")
        for path in ("tools/audit_baldosa_romless_candidate.py",
                     "tests/unit/test_audit_baldosa_romless_candidate.py"):
            self.assertIn(f'"{path}"', routed)

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

    def test_windows_smoke_pr_uses_one_ready_reusable_caller(self):
        text = (WORKFLOWS / "windows-native-smoke.yml").read_text()
        wrapper = (WORKFLOWS / "qa05-qa09-windows-candidate.yml").read_text()
        self.assertTrue(_pushes_main(text))
        self.assertEqual(_block(text, "pull_request").strip(), "")
        self.assertIn('      - ".github/workflows/windows-native-smoke.yml"',
                      _block(wrapper, "pull_request"))
        self.assertIn(
            "uses: ./.github/workflows/windows-native-smoke.yml", wrapper,
        )
        self.assertIn(
            "github.event.pull_request.draft == false", wrapper,
        )
        self.assertIn("  workflow_call:\n", text)
        self.assertIn(
            "if: github.event_name != 'pull_request' || "
            "github.event.pull_request.head.repo.full_name == github.repository",
            text,
        )

    def test_results_navigation_shared_fanout_is_bounded(self):
        text = (WORKFLOWS / "modern-shared-native-acceptance.yml").read_text()
        block = text.split("  results-navigation:", 1)[1].split("  ordinary-2p:", 1)[0]
        match = re.search(r"shard:\s*\[([^\]]+)\]", block)
        self.assertIsNotNone(match)
        shards = [item.strip() for item in match.group(1).split(",")]
        self.assertEqual(shards, ["selection", "progression", "isolation"])
        self.assertIn("needs: build", block)
        self.assertNotIn("cmake --build", block)

    def test_native_ui_evidence_scope_is_bounded(self):
        text = (WORKFLOWS / "native-ui-evidence.yml").read_text()
        self.assertNotIn('"native/product/**"', text)
        self.assertIn("fail-fast: false", text)
        match = re.search(r"shard:\s*\[([^\]]+)\]", text)
        self.assertIsNotNone(match)
        shards = [item.strip() for item in match.group(1).split(",")]
        self.assertEqual(
            shards,
            ["core", "navigation", "results-a", "results-b", "records", "profiles"],
        )
        self.assertLessEqual(len(shards), 6)


    def test_onboarding_core_fanout_is_bounded_and_build_free(self):
        text = (WORKFLOWS / "modern-onboarding-practice-acceptance.yml").read_text()
        block = text.split("  core-acceptance:", 1)[1].split(
            "  independent-acceptance:", 1
        )[0]
        match = re.search(r"shard:\s*\[([^\]]+)\]", block)
        self.assertIsNotNone(match)
        shards = [item.strip() for item in match.group(1).split(",")]
        self.assertEqual(
            shards,
            ["onboarding-rematch", "practice", "system"],
        )
        self.assertIn("needs: build", block)
        self.assertNotIn("cmake --build", block)
        self.assertIn("Seed dismissed onboarding for independent core shards", block)

    def test_onboarding_acceptance_does_not_trigger_on_docs_only(self):
        text = (WORKFLOWS / "modern-onboarding-practice-acceptance.yml").read_text()
        self.assertNotIn('"docs/MODERN-PRODUCT-LAYER.md"', _block(text, "pull_request"))


    def test_onboarding_uses_one_candidate_with_bounded_fanout(self):
        text = (WORKFLOWS / "modern-onboarding-practice-acceptance.yml").read_text()
        self.assertIn("  build:", text)
        self.assertIn("modern-onboarding-native-candidate", text)
        self.assertIn("  core-acceptance:", text)
        self.assertIn("  independent-acceptance:", text)
        independent = text.split("  independent-acceptance:", 1)[1]
        match = re.search(r"shard:\s*\[([^\]]+)\]", independent)
        self.assertIsNotNone(match)
        shards = [item.strip() for item in match.group(1).split(",")]
        self.assertEqual(
            shards,
            ["tour-a", "tour-b", "feedback-parity", "feedback-aux", "multiplayer"],
        )
        self.assertLessEqual(len(shards), 5)
        consumer = text.split("  core-acceptance:", 1)[1]
        self.assertIn("Install native runtime dependencies", consumer)
        runtime_install = consumer.split(
            "- name: Install native runtime dependencies", 1
        )[1].split("- name:", 1)[0]
        self.assertIn("xvfb xdotool", runtime_install)
        self.assertNotIn("-dev", runtime_install)
        self.assertNotIn("cmake", runtime_install)
        self.assertNotIn("ninja", runtime_install)


    def test_onboarding_feedback_split_preserves_vibration_parity(self):
        workflow = (WORKFLOWS / "modern-onboarding-practice-acceptance.yml").read_text()
        harness = Path("tests/native/run_modern_vibration_acceptance.sh").read_text()
        independent = workflow.split("  independent-acceptance:", 1)[1]
        self.assertIn("feedback-parity", independent)
        self.assertIn("feedback-aux", independent)
        self.assertIn("run_modern_vibration_acceptance.sh vibration-parity parity", independent)
        self.assertIn("run_modern_vibration_acceptance.sh vibration-aux aux", independent)
        self.assertIn("[parity|aux|all]", harness)
        self.assertIn('MODE="${4:-all}"', harness)

    def test_local_multiplayer_contract_does_not_trigger_on_docs_only(self):
        text = (WORKFLOWS / "local-multiplayer-product-contracts.yml").read_text()
        self.assertNotIn('"docs/LOCAL-MULTIPLAYER-SETUP.md"', _block(text, "pull_request"))


    def test_widescreen_4x3_uses_one_build_with_bounded_route_fanout(self):
        text = (WORKFLOWS / "widescreen-4x3-regression.yml").read_text()
        self.assertIn("  build:", text)
        self.assertIn("  routes:", text)
        routes = text.split("  routes:", 1)[1].split("  aggregate:", 1)[0]
        match = re.search(r"route:\s*\[([^\]]+)\]", routes)
        self.assertIsNotNone(match)
        shards = [item.strip() for item in match.group(1).split(",")]
        self.assertEqual(shards, ["one-player", "vs", "two-player"])
        self.assertIn("needs: build", routes)
        self.assertNotIn("cmake --build", routes)
        self.assertIn("widescreen-4x3-candidates", routes)

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
        # Windows smoke is the sole justified exception: its first main run
        # publishes a source-bound ROM-free PE after the producer YAML merges.
        # A PR-merge test cannot supply that exact-main executable witness.
        allowed = {"windows-native-smoke.yml"}
        offenders = []
        for path in _workflow_paths():
            text = path.read_text()
            push = _block(text, "push")
            own_path = f'.github/workflows/{path.name}'
            if _pushes_main(text) and own_path in push and path.name not in allowed:
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            f"only the Windows exact-main PE producer may self-trigger on main: {offenders}",
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


    def test_main_push_windows_producer_is_read_only(self):
        # This sole main-push exception builds/boots Windows; it does not
        # publish Git contents. Never use a DOTALL nested-line regex here:
        # on a long workflow with contents: read and no contents: write it
        # catastrophically backtracks and times out the entire unit job.
        self.assertEqual(MAIN_PUSH_ALLOWLIST, {"windows-native-smoke.yml"})
        text = (WORKFLOWS / "windows-native-smoke.yml").read_text()
        self.assertFalse(_block(text, "pull_request"))
        self.assertTrue(_pushes_main(text))
        self.assertRegex(text, r"(?m)^permissions:\n  contents: read[ \t]*$")
        self.assertNotRegex(text, r"(?m)^  contents: write[ \t]*$")

    def test_windows_reusable_callers_do_not_cancel_one_another(self):
        # Only the QA wrapper now triggers when smoke YAML changes on a
        # ready, same-repo PR. The called workflow still has its own
        # main-push and manual routes, not an expensive second PR trigger.
        text = (WORKFLOWS / "windows-native-smoke.yml").read_text()
        qa05 = (WORKFLOWS / "qa05-qa09-windows-candidate.yml").read_text()
        self.assertNotIn("\n  pull_request:\n", text)
        self.assertIn('      - ".github/workflows/windows-native-smoke.yml"', qa05)
        self.assertIn("  pull_request:\n", qa05)
        self.assertIn("github.event.pull_request.draft == false", qa05)
        self.assertIn("  workflow_call:\n", text)
        self.assertIn("  workflow_dispatch:\n", text)
        self.assertIn(
            "uses: ./.github/workflows/windows-native-smoke.yml", qa05
        )
        self.assertIn(
            "group: windows-native-smoke-${{ github.workflow }}-${{ github.ref }}",
            text,
        )
        self.assertIn("cancel-in-progress: true", text)


if __name__ == "__main__":
    unittest.main()
