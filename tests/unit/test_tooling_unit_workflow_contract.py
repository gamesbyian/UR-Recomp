import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "tooling-unit-tests.yml"

PURE_MODEL_PATHS = (
    "native/product/completed_run_ghost_target.hpp",
    "native/product/display_treatment_policy.hpp",
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

        self.assertIn(
            "python3 -m unittest discover -s tests/unit -p 'test_*.py' -v",
            workflow,
        )

    def test_trigger_scope_stays_narrow(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn('- "native/product/**"', workflow)


if __name__ == "__main__":
    unittest.main()
