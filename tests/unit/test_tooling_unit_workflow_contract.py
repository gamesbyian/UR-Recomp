import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "tooling-unit-tests.yml"

PURE_MODEL_PATHS = (
    "native/product/completed_run_ghost_target.hpp",
    "native/product/display_treatment_policy.hpp",
    "native/product/modern_controller_prompt.hpp",
    "native/product/reduced_flashing_frame_blend.hpp",
    "native/product/run_artifact_date.hpp",
    "native/product/run_artifact_date.cpp",
    "tests/native/run_artifact_date_test.cpp",
    "native/product/reduced_flashing_frame_blend.cpp",
    "tests/native/reduced_flashing_frame_blend_test.cpp",
    "tests/native/modern_controller_prompt_test.cpp",
    "tests/native/display_treatment_policy_test.cpp",
    "tests/native/completed_run_ghost_target_test.cpp",
    "native/product/local_multiplayer_setup.hpp",
    "native/product/modern_host_input_release_latch.hpp",
    "native/product/modern_root_menu.hpp",
    "native/product/modern_text_catalog.hpp",
    "native/product/modern_text_layout.hpp",
    "tests/native/local_multiplayer_setup_test.cpp",
    "tests/native/modern_host_input_release_latch_test.cpp",
    "tests/native/modern_root_menu_test.cpp",
    "tests/native/modern_text_catalog_test.cpp",
    "tests/native/modern_text_layout_test.cpp",
)


class ToolingUnitWorkflowContractTests(unittest.TestCase):
    def test_cancelled_suite_preserves_unfinished_shard_diagnostics(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if: failure() || cancelled()", workflow)
        self.assertIn("name: ci-tooling-unit-failure-logs", workflow)
        self.assertIn("path: ${{ runner.temp }}/unit-shard*.log", workflow)

    def test_pure_product_models_trigger_their_unit_wrappers(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for path in PURE_MODEL_PATHS:
            self.assertIn(f'- "{path}"', workflow)

        # The dependency-free Python suite may be sharded for wall-clock speed,
        # but the partitioner must enumerate every test_*.py deterministically
        # and assign each discovered module to exactly one shard (see
        # test_partition_unit_tests.py), and the workflow must fail if any
        # shard fails.
        self.assertIn("tools/partition_unit_tests.py", workflow)
        self.assertIn('python3 tools/run_unit_shard.py --out', workflow)
        self.assertIn('"${mods[@]}" >"$RUNNER_TEMP/unit-shard$i.log" 2>&1 &', workflow)
        self.assertIn('unit-module-timings-shard$i.json', workflow)
        # The new runner must retain one global unittest exit/verdict and
        # never substitute a timing receipt for actual test-suite completion.
        runner = (ROOT / "tools" / "run_unit_shard.py").read_text(encoding="utf-8")
        self.assertIn("unittest.TextTestRunner(verbosity=2)", runner)
        self.assertIn("result.wasSuccessful()", runner)
        self.assertIn("result, measured = execute(args.modules)", runner)
        self.assertIn('wait "${pids[$i]}"; r=$?', workflow)
        self.assertIn('test "$rc" -eq 0', workflow)

    def test_draft_syntax_and_ready_full_unit_are_disjoint(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "types: [opened, reopened, synchronize, ready_for_review, converted_to_draft]",
            workflow)
        self.assertIn("  workflow_dispatch:", workflow)
        self.assertIn("jobs:\n  unit:\n", workflow)
        unit = workflow.split("jobs:\n  unit:\n", 1)[1].split(
            "\n  draft-syntax:\n", 1)[0]
        draft = workflow.split("\n  draft-syntax:\n", 1)[1]
        self.assertIn(
            "if: github.event_name != 'pull_request' || "
            "github.event.pull_request.draft == false", unit)
        self.assertIn(
            "if: github.event_name == 'pull_request' && "
            "github.event.pull_request.draft == true", draft)
        self.assertIn("Run full dependency-free Python unit tests", unit)
        self.assertIn("tools/run_unit_shard.py --out", unit)
        self.assertIn("python3 -m compileall -q tests/unit tools", draft)
        self.assertIn("YAML.parse_file(path)", draft)
        self.assertIn("DRAFT_SYNTAX_ONLY", draft)
        self.assertNotIn("tools/run_unit_shard.py", draft)
        # Draft may run direct, small Python test modules; it may not
        # pretend that discovery, all-unit sharding or full coverage happened.
        self.assertIn("DRAFT_TARGETED_DIAGNOSTIC_ONLY", draft)
        self.assertIn("tools/ci_draft_target_tests.py", draft)
        self.assertIn('timeout 45s python3 -m unittest -v "${mods[@]}"', draft)
        self.assertNotIn("tools/partition_unit_tests.py", draft)
        self.assertNotIn("tools/run_unit_shard.py", draft)

    def test_trigger_scope_stays_narrow(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn('- "native/product/**"', workflow)


if __name__ == "__main__":
    unittest.main()
