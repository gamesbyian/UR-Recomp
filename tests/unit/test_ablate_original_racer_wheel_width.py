"""Cheap deterministic tests for read-only ART-4K wheel/rim width ablation."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "tools/art/ablate_original_racer_wheel_width.py"
spec = importlib.util.spec_from_file_location("wheel_hypothesis", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class WheelAblationTests(unittest.TestCase):
    def test_only_two_registered_part_families_can_change(self):
        for name in ("tire__material_0", "tire__material_1",
                     "rim_and_hub__material_4"):
            self.assertTrue(module.wheel_node(name))
        for name in ("fork_and_frame__material_0", "saddle__material_1",
                     "pedals__material_2", "tire", "rim_and_hub",
                     "fake_tire__material_0", ""):
            self.assertFalse(module.wheel_node(name))

    def test_fixed_factors_have_unchanged_baseline_and_bounded_range(self):
        self.assertIn(1.0, module.FACTORS)
        self.assertEqual(len(module.FACTORS), len(set(module.FACTORS)))
        self.assertTrue(all(type(f) is float and .85 <= f <= 1.35
                            for f in module.FACTORS))
        self.assertFalse(module.FACTORS[0] == module.FACTORS[-1])

    def test_selective_world_x_transform_preserves_others_and_input(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest("optional NumPy not installed")
        original = np.array([[1.0, 2.0, 3.0], [-2.0, -1.0, 4.0]])
        for name in ("saddle__material_0", "pedals__material_0"):
            unchanged = module.scale_component_x(original, name, 1.1)
            self.assertTrue(np.array_equal(unchanged, original))
            self.assertIsNot(unchanged, original)
        scaled = module.scale_component_x(original, "tire__material_0", 1.1)
        self.assertTrue(np.array_equal(original, np.array([[1.,2.,3.],[-2.,-1.,4.]])))
        self.assertTrue(np.allclose(scaled[:,0], [1.1,-2.2]))
        self.assertTrue(np.array_equal(scaled[:,1:], original[:,1:]))

    def test_fail_closed_on_unbounded_and_nonfinite_samples(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest("optional NumPy not installed")
        vertices = np.array([[1., 2., 3.]])
        for factor in (0.0, .50, 1.60, float("nan"), float("inf"), 1, "1.1"):
            with self.subTest(factor=factor), self.assertRaises(ValueError):
                module.scale_component_x(vertices, "tire__material_0", factor)
        for invalid in (np.zeros((3,2)), np.array([[np.inf,0.,0.]]),
                        np.array([1.,2.,3.])):
            with self.assertRaises(ValueError):
                module.scale_component_x(invalid, "tire__material_0", 1.1)

    def test_no_source_or_model_claims_are_injected_by_selector(self):
        self.assertFalse(module.wheel_node("fork_and_frame__material_0"))
        self.assertFalse(module.wheel_node("saddle__material_0"))
        self.assertEqual(module.SCHEMA, "UR-RACER-REAL-GLB-WHEEL-X-ABLATION/1")


if __name__ == "__main__":
    unittest.main()
