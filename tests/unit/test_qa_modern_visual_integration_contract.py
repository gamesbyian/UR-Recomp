"""Rom-free regression of the combined Modern native visual-hook inventory.

A passing *synthetic source contract* is not an actual compiled/native run.
"""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools import qa_modern_visual_integration_contract as check


FIXTURE = {
    "native/product/modern_title_presenter.hpp": "render_modern_title(",
    "native/product/modern_menu_visual_grammar.hpp": "modern_menu_paint_focus_band(",
    "native/product/modern_native_destination_presenter.hpp": "render_modern_native_destination(",
    "native/product/modern_menu_motion.hpp": "advance_modern_menu_motion(",
    "tools/baldosa_native_modern_root.cpp": """
ur::product::render_modern_title(
ur::product::render_modern_native_destination(
ur::product::advance_modern_menu_motion(
ur::product::paint_modern_menu_selection_motion(
modern_title_confirm(
modern_title_active(
*logical_width = ur::product::modern_title_logical_width(
if (width != 342) return;
g_navigation_edges.p1_gamepad(
g_navigation_edges.keyboard(
std::strcmp(mode, "authentic")
UR_REDUCED_MOTION
const int panel_w = width == 342 ? 320 : 240;
const HostOverlayRect root_rect{(width - panel_w) / 2,10,panel_w,204};
""",
    "tools/baldosa_modern_profile_activation_spike.py": """
.native_widescreen = 1
.prepare_frame = ur_baldosa_modern_root_prepare_frame
""",
}


class ModernCombinedNativeHooksTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel, source in FIXTURE.items():
            file = self.root / rel
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(source, encoding="utf-8")

    def test_complete_fake_hook_inventory_remains_zero_approval(self):
        result = check.inventory(self.root)
        self.assertTrue(result["eligible_for_native_acceptance_run"])
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["missing_native_integration_hooks"], [])
        self.assertEqual(result["known_host_geometry_conflicts"], [])
        self.assertFalse(result["native_executed"])
        self.assertEqual(result["screenshots_captured"], 0)
        self.assertFalse(result["human_visual_approved"])
        self.assertFalse(result["authentic_isolation_approved"])
        self.assertEqual(result["release_gate_credit"], 0)

    def test_destination_drop_from_combined_host_is_detected(self):
        file = self.root / "tools/baldosa_native_modern_root.cpp"
        file.write_text(FIXTURE[file.relative_to(self.root).as_posix()].replace(
            "ur::product::render_modern_native_destination(", ""), encoding="utf-8")
        result = check.inventory(self.root)
        self.assertFalse(result["eligible_for_native_acceptance_run"])
        self.assertIn("native_destinations_drawn", result["missing_native_integration_hooks"])
        self.assertTrue(result["checked"]["destination_renderer_available"]["present"])

    def test_missing_motion_hook_and_guest_mode_guard_detected(self):
        file = self.root / "tools/baldosa_native_modern_root.cpp"
        file.write_text(FIXTURE[file.relative_to(self.root).as_posix()].replace(
            "ur::product::advance_modern_menu_motion(", "").replace(
            'std::strcmp(mode, "authentic")', ""), encoding="utf-8")
        result = check.inventory(self.root)
        self.assertIn("native_motion_updated", result["missing_native_integration_hooks"])
        self.assertIn("authentic_mode_can_disable_root",
                      result["missing_native_integration_hooks"])

    def test_unmerged_240px_motion_rect_rejected_with_other_hooks_present(self):
        file = self.root / "tools/baldosa_native_modern_root.cpp"
        source = FIXTURE[file.relative_to(self.root).as_posix()]
        source += ("\nur::product::paint_modern_menu_selection_motion("
                   "painter, pixels, stride, height, 1, "
                   "HostOverlayRect{(width - 240) / 2, 10, 240, 204}, phase);")
        file.write_text(source, encoding="utf-8")
        result = check.inventory(self.root)
        self.assertEqual(result["missing_native_integration_hooks"], [])
        self.assertFalse(result["eligible_for_native_acceptance_run"])
        self.assertEqual(result["known_host_geometry_conflicts"],
                         ["motion_uses_240px_root_under_342px_child_canvas"])

    def test_variable_name_does_not_hide_fixed_wide_motion_geometry(self):
        file = self.root / "tools/baldosa_native_modern_root.cpp"
        source = FIXTURE[file.relative_to(self.root).as_posix()]
        source = source.replace(
            "const int panel_w = width == 342 ? 320 : 240;\n"
            "const HostOverlayRect root_rect{(width - panel_w) / 2,10,panel_w,204};",
            "const HostOverlayRect root_rect{8,10,240,204};")
        source += ("\nur::product::paint_modern_menu_selection_motion("
                   "painter, pixels, stride, height, 1, root_rect, phase);")
        file.write_text(source, encoding="utf-8")
        result = check.inventory(self.root)
        self.assertEqual(result["missing_native_integration_hooks"], [])
        self.assertEqual(result["known_host_geometry_conflicts"], [
            "motion_and_destination_share_fixed_240px_root_on_wide_canvas"])
        self.assertFalse(result["eligible_for_native_acceptance_run"])

    def test_motion_using_shared_root_rect_is_eligible_to_be_run(self):
        file = self.root / "tools/baldosa_native_modern_root.cpp"
        source = FIXTURE[file.relative_to(self.root).as_posix()]
        source += ("\nur::product::paint_modern_menu_selection_motion("
                   "painter, pixels, stride, height, 1, root_rect, phase);")
        file.write_text(source, encoding="utf-8")
        result = check.inventory(self.root)
        self.assertEqual(result["known_host_geometry_conflicts"], [])
        self.assertTrue(result["eligible_for_native_acceptance_run"])

    def test_missing_source_module_and_symlink_rejected(self):
        file = self.root / "native/product/modern_title_presenter.hpp"
        file.unlink()
        self.assertIn("title_renderer_available", check.inventory(self.root)["missing"])
        file.symlink_to(self.root / "tools/baldosa_native_modern_root.cpp")
        self.assertFalse(check.inventory(self.root)["checked"]["title_renderer_available"]["present"])

    def test_all_project_authorities_have_deterministic_names(self):
        self.assertGreaterEqual(len(check.REQUIREMENTS), 15)
        self.assertEqual(len(check.REQUIREMENTS), len(set(check.REQUIREMENTS)))
        self.assertTrue(set(check.REQUIRED_NATIVE).issubset(check.REQUIREMENTS))
        # This QA tool reads (never mutates) only first-party paths.
        for path, pattern in check.REQUIREMENTS.values():
            self.assertNotIn("..", Path(path).parts)
            self.assertTrue(pattern)


if __name__ == "__main__":
    unittest.main()
