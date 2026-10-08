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
    "native/product/modern_root_menu.hpp",
    "native/product/modern_text_catalog.hpp",
    "native/product/modern_text_layout.hpp",
    "tests/native/local_multiplayer_setup_test.cpp",
    "tests/native/modern_root_menu_test.cpp",
    "tests/native/modern_text_catalog_test.cpp",
    "tests/native/modern_text_layout_test.cpp",
)


class ToolingUnitWorkflowContractTests(unittest.TestCase):
    def test_pure_product_models_trigger_their_unit_wrappers(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for path in PURE_MODEL_PATHS:
            self.assertIn(f'- "{path}"', workflow)

        # The dependency-free Python suite may be sharded for wall-clock speed,
        # but discovery must still enumerate every test_*.py deterministically
        # and assign each discovered module to exactly one shard.
        self.assertIn(
            "find tests/unit -maxdepth 1 -type f -name 'test_*.py'",
            workflow,
        )
        self.assertIn("| sort", workflow)
        self.assertIn('module="tests.unit.${test_file%.py}"', workflow)
        self.assertIn("sha256sum", workflow)
        self.assertIn("16#$first_byte % 2 == 0", workflow)
        self.assertIn('python3 -m unittest -v "$@"', workflow)
        self.assertIn('wait "$p0"; r0=$?', workflow)
        self.assertIn('wait "$p1"; r1=$?', workflow)

    def test_trigger_scope_stays_narrow(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn('- "native/product/**"', workflow)


if __name__ == "__main__":
    unittest.main()
