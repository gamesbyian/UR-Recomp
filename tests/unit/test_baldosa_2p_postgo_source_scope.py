"""QA-08 post-GO original 2P racer source opt-in is diagnostic only."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PRESENTER = ROOT / "native/presentation/racer_hd_presenter.cpp"
WORKFLOW = ROOT / ".github/workflows/baldosa-core-spike.yml"


class PostGo2POriginalObjSourceScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        native = PRESENTER.read_text(encoding="utf-8")
        cls.source_dump = native[
            native.index("void dump_wide_obj_source() noexcept {"):
            native.index("bool p1_only_capture_enabled() noexcept {")
        ]
        cls.native_mode = native[
            native.index("if (!racer_hd_can_capture_frame_geometry("):
            native.index("const SelectionResult p1 =", native.index(
                "if (!racer_hd_can_capture_frame_geometry("))
        ]
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_new_source_frame_is_opt_in_only_and_keeps_three_prior_frames(self):
        body = self.source_dump
        self.assertIn('std::getenv("UR_RACER_HD_WIDE_SOURCE_POST_GO_FRAME")', body)
        self.assertIn('std::getenv("UR_RACER_HD_WIDE_SOURCE_FRAME")', body)
        self.assertIn('std::getenv("UR_RACER_HD_WIDE_SOURCE_EXTRA_FRAME")', body)
        self.assertIn('std::getenv("UR_RACER_HD_WIDE_SOURCE_LAST_FRAME")', body)
        self.assertIn('matches_frame(post_go, g_sim_frame)', body)
        self.assertIn('if (!requested || !*requested || !directory || !*directory) return;', body)

    def test_extra_source_snapshot_never_arms_destructive_ppu_capture(self):
        self.assertNotIn("RemoveFromGame", self.source_dump)
        self.assertNotIn("PpuSetOverlayCapture", self.source_dump)
        self.assertIn("UR_RACER_HD_WIDE_SOURCE", self.source_dump)
        # Source capture cannot alone arm the separate real native
        # counterfactual RemoveFromGame control or a host HD paint.
        self.assertIn("wide_source_probe_slot()", self.native_mode)
        self.assertIn("kPpuOverlayFlag_RemoveFromGame : 0", self.native_mode)
        self.assertIn("racer_hd_can_capture_frame_geometry", PRESENTER.read_text())

    def test_native_postgo_report_uses_existing_four_2p_slot_guest_routes(self):
        workflow = self.workflow
        start = workflow.index("for slot in 96 97 98 99; do")
        end = workflow.index("\n          done", start)
        body = workflow[start:end]
        self.assertIn(
            'export UR_RACER_HD_WIDE_SOURCE_POST_GO_FRAME=2208',
            workflow[:start])
        self.assertIn(
            'export UR_BALDOSA_WS342_LATE_CAPTURE_AFTER=2200',
            workflow[:start])
        self.assertIn(
            'ur-baldosa-ws342-obj-slot$slot-frame002208.pam', body)
        self.assertIn('ws342_obj_slot_${slot}_frame2208.json', body)
        self.assertIn("--slot \"$slot\" --min-shared 7", body)
        self.assertEqual(body.count("bash baldosa/tools/run_route.sh"), 1)
        self.assertEqual(body.count("cmp \"$RUNNER_TEMP"), 1)
        self.assertIn("ws342_obj_slot_${slot}_frame1888.json", body)
        self.assertIn("ws342_obj_slot_${slot}_frame1872.json", body)

    def test_source_postgo_scope_cleared_before_removal_diagnostics(self):
        workflow = self.workflow
        start = workflow.index("for slot in 96 97 98 99; do")
        end = workflow.index("# Diagnostic final-composite attribution", start)
        between = workflow[start:end]
        self.assertIn("unset UR_RACER_HD_WIDE_SOURCE_POST_GO_FRAME", between)
        self.assertIn("unset UR_BALDOSA_WS342_LATE_CAPTURE_AFTER", between)
        self.assertIn('ws342_obj_slot_96_frame2208.json', workflow)
        self.assertIn('ws342_obj_slot_99_frame2208.json', workflow)
        self.assertIn(
            'baldosa-ws342-obj-slots/ur-baldosa-ws342-obj-slot*.pam',
            workflow)


if __name__ == "__main__":
    unittest.main()
