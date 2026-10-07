import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKFLOW = (
    ROOT / ".github" / "workflows" / "regional-retail-frontend-comparison.yml"
)


class RegionalDenseMotionWorkflowContractTests(unittest.TestCase):
    def test_dense_title_motion_is_opt_in_and_retained(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("dense_title_motion:", workflow)
        self.assertIn('default: false', workflow)
        self.assertIn('if: ${{ inputs.dense_title_motion }}', workflow)
        self.assertIn('--case title-motion', workflow)
        self.assertIn(
            'dense-title-motion/dumps/title-motion/usa',
            workflow,
        )
        self.assertIn(
            'dense-title-motion/dumps/title-motion/europe',
            workflow,
        )
        self.assertEqual(
            workflow.count("tools/analyze_frontend_transition_sequence.py"),
            2,
        )
        self.assertIn(
            'path: ${{ runner.temp }}/regional-frontend/',
            workflow,
        )

    def test_default_comparison_step_does_not_request_dense_case(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        ordinary_start = workflow.index(
            "- name: Capture and compare retail frontends"
        )
        dense_start = workflow.index(
            "- name: Capture dense title transition motion evidence"
        )
        ordinary = workflow[ordinary_start:dense_start]
        self.assertNotIn("--case title-motion", ordinary)


if __name__ == "__main__":
    unittest.main()
