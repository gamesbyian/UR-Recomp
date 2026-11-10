"""Keep the actual five-GLB browser acceptance reachable on PR promotion.

The atlas PR workflow has inexpensive draft jobs plus an expensive real-model
job. A draft-only success cannot certify that job; ready_for_review must fire
its full product consumer on the same source head.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/windows-visual-atlas-pr-validate.yml"


class AtlasReadyGateTests(unittest.TestCase):
    def test_ready_transition_runs_actual_model_export(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        trigger = source.split("\non:\n", 1)[1].split("\npermissions:\n", 1)[0]
        self.assertIn(
            "types: [opened, reopened, synchronize, ready_for_review]", trigger
        )
        self.assertIn('"tools/art/model-review/**"', trigger)
        self.assertIn("  experimental-real-model-export:\n", source)
        self.assertIn("  classify-source:\n", source)
        self.assertIn("      model: ${{ steps.detect.outputs.model }}", source)
        self.assertIn(
            "    if: github.event.pull_request.draft == false && needs.classify-source.outputs.model == 'true'\n",
            source,
        )
        self.assertIn("UR_MODEL_SMOKE_REAL=1 node", source)


if __name__ == "__main__":
    unittest.main()
