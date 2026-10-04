import unittest
from tools.check_work_queue_density import oversized_blocks

class WorkQueueDensityTest(unittest.TestCase):
    def test_reports_only_oversized_blocks(self):
        text = "short\n\n" + ("x" * 20) + "\n\nsmall"
        self.assertEqual(oversized_blocks(text, 10), [("xxxxxxxxxxxxxxxxxxxx", 20)])

if __name__ == "__main__":
    unittest.main()
