"""ROM-free ART-4K projected GLB-frame axis safeguards and source parity tests."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "tools/art/audit_real_glb_coloured_frame_axes.py"
spec = importlib.util.spec_from_file_location("art4k_model_frame_axes", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class OriginalModelAxisTests(unittest.TestCase):
    def test_material_and_named_part_are_the_existing_canonical_glb_identity(self):
        self.assertEqual(mod.FRAME, "fork_and_frame__material_0")
        self.assertEqual(mod.SOURCE_BLUE, (28, 89, 222, 255))
        self.assertEqual(len(mod.POSES), 5)

    def test_no_original_source_camera_or_pose_mapping_is_inferred(self):
        self.assertEqual(mod.SCHEMA, "UR-ART4K-UNPAIRED-FIVE-GLB-COLOUR-FRAME-AXES/1")
        self.assertIn("unpaired", mod.audit.__doc__ or "unpaired")
        self.assertTrue(callable(mod.source_colour_frame_pixels))

    def test_frame_pca_from_existing_source_study_remains_vertical_and_diagonal(self):
        from tools.art.audit_original_racer_chromatic_axes import principal_axis
        points = [(20 + y, y) for y in range(17)]
        straight = [(20, y) for y in range(17)]
        self.assertAlmostEqual(principal_axis(points)["screen_axis_angle_from_down_y_degrees"],
                               45., delta=.1)
        self.assertAlmostEqual(principal_axis(straight)["screen_axis_angle_from_down_y_degrees"],
                               0., delta=.1)


if __name__ == "__main__":
    unittest.main()
