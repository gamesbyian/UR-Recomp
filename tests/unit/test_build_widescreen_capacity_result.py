import unittest
from tools.build_widescreen_capacity_result import build_result

class WidescreenCapacityResultTest(unittest.TestCase):
    def test_builds_dynamic_margin_result(self):
        row = {"slot1":{"x":1},"slot2":{"x":2},"race_progress":{"lap":1},"camera_and_viewport":{"x":3}}
        result = build_result({"a":row},{"a":row},[256,224],[352,224],48)
        self.assertTrue(result["geometry_accepted"])
        self.assertTrue(result["protected_state_equal_at_all_checkpoints"])
        self.assertEqual(result["capacity_classification"], "vs-plus48-live-course-capacity-proven")
        self.assertEqual(result["plus48_frame_geometry"], [352,224])

if __name__ == "__main__":
    unittest.main()
