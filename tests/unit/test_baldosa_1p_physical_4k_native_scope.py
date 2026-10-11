"""QA-10 live 1P true-SDL-3840 capture stays bounded and source-faithful.

Structural regression for the existing pinned AOT workflow. The existing
native physical-output oracle tests every byte of captured output; this
test prevents the 1P route from degrading into a fake 4x texture assertion,
untracked 2P run, artist-likeness waiver, or independent build/harness.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/baldosa-core-spike.yml"
ORACLE = ROOT / "tools/check_baldosa_physical_4k_capture.py"


class LiveOnePlayerPhysical4kNativeScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        first = cls.workflow.index(
            "# QA-10 independent *live one-player widened* physical SDL")
        last = cls.workflow.index(
            "# Independent Original 256x224 1x source, 1024x896 4x guest",
            first)
        cls.block = cls.workflow[first:last]

    def test_only_one_existing_original_1p_guest_route_added(self):
        block = self.block
        self.assertEqual(block.count("bash baldosa/tools/run_route.sh"), 1)
        self.assertIn("baldosa/tests/routes/race_1p.txt", block)
        self.assertNotIn("race_2p_split.txt", block)
        self.assertNotIn("cmake ", block)
        self.assertNotIn("make ", block)
        self.assertIn("UR_BALDOSA_WS342_LIVE=1", block)
        self.assertIn("UR_BALDOSA_HD_DENSITY=4", block)
        self.assertIn("UR_BALDOSA_WS342_LATE_CAPTURE_AFTER=2200", block)
        self.assertIn("UR_BALDOSA_WS342=1", block)

    def test_genuine_physical_4k_readback_not_density_only(self):
        block = self.block
        self.assertIn('DISPLAY=:100 TMO=240 bash baldosa/tools/run_route.sh', block)
        self.assertIn('UR_BALDOSA_PHYSICAL_4K_CAPTURE_FRAME=2208', block)
        self.assertIn('UR_BALDOSA_PHYSICAL_4K_CAPTURE_FILE=', block)
        self.assertIn('source=SDL_RenderReadPixels status=saved', block)
        self.assertIn('test -s "$UR_BALDOSA_PHYSICAL_4K_CAPTURE_FILE"', block)
        self.assertIn('python3 tools/check_baldosa_physical_4k_capture.py', block)
        self.assertIn('--source "$RUNNER_TEMP/baldosa-ws342-live-1p/', block)
        self.assertIn('--density-4x "$RUNNER_TEMP/baldosa-ws342-live-1p-4x/', block)
        self.assertIn('--physical-4k "$UR_BALDOSA_PHYSICAL_4K_CAPTURE_FILE"', block)
        self.assertIn('--frame "$UR_BALDOSA_PHYSICAL_4K_CAPTURE_FRAME"', block)
        oracle = ORACLE.read_text(encoding="utf-8")
        self.assertIn("3840, 2160", oracle)
        self.assertIn("_verify_physical(src, physical, logical_width)", oracle)

    def test_complete_original_1p_crc_and_source_only_checks(self):
        block = self.block
        self.assertIn('race_1p_ur_ws342_live_physical_4k/fd/crc.txt', block)
        self.assertIn('race_1p/fd/crc.txt', block)
        self.assertIn('cmp "$RUNNER_TEMP/baldosa-evidence/race_1p/fd/crc.txt"', block)
        self.assertIn('python3 tools/check_baldosa_wide_density_parity.py', block)
        self.assertIn('--min-shared 3', block)
        self.assertIn('UR_BALDOSA_WS342_CAPTURE_DIR="$RUNNER_TEMP/baldosa-1p-live-physical-4k-source"', block)
        self.assertIn('baldosa-ws342-live-1p/ur-baldosa-ws342-002208.pam', block)
        self.assertIn('baldosa-ws342-live-1p-4x/ur-baldosa-ws342-002208.pam', block)
        self.assertNotIn('UR_RACER_HD_WIDE_REMOVE_DIAGNOSTIC=counterfactual', block)
        self.assertNotIn('UR_RACER_HD_WIDE_REMOVE_SLOT=', block)
        self.assertNotIn('UR_RACER_HD_WIDE_REMOVE_PAIR=', block)

    def test_capture_knobs_cleared_and_outputs_archived(self):
        block = self.block
        self.assertIn('unset UR_BALDOSA_PHYSICAL_4K_CAPTURE_FRAME UR_BALDOSA_PHYSICAL_4K_CAPTURE_FILE', block)
        self.assertIn('unset UR_BALDOSA_WS342_LIVE UR_BALDOSA_WS342_LATE_CAPTURE_AFTER', block)
        self.assertIn('ws342_live_1p_physical_4k_frame2208.json', block)
        self.assertIn('ws342_live_1p_physical_source_density_parity.json', block)
        archive = self.workflow[self.workflow.index("upload-artifact@"):]
        self.assertIn('baldosa-evidence/ws342_live_1p_physical_4k_frame2208.json', archive)
        self.assertIn('baldosa-evidence/ws342_live_1p_physical_source_density_parity.json', archive)

    def test_no_absolute_frame_rule_spread_into_automatic_workflow(self):
        import re
        # Required guest frame is a validated control, never a new CI log
        # assertion in the form barred by the live-trigger policy.
        self.assertIsNone(re.search(r'\bframe=\d+', self.block))
        self.assertNotIn('SNESRECOMP_SCREENSHOT_FRAME=', self.block)


if __name__ == "__main__":
    unittest.main()
