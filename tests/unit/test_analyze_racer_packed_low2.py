import unittest

from tools.analyze_racer_packed_low2 import LIST_START, LIST_END


class RacerPackedLow2Tests(unittest.TestCase):
    def test_listing_bounds_are_renderer_local(self):
        self.assertEqual(LIST_START, "83:F190")
        self.assertEqual(LIST_END, "83:F290")


if __name__ == "__main__":
    unittest.main()
