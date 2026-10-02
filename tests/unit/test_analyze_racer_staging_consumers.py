import unittest
from tools.analyze_racer_staging_consumers import TARGETS

class RacerStagingConsumerTests(unittest.TestCase):
    def test_expected_targets(self):
        self.assertEqual(TARGETS["piece_source_stage"],0x1645)
        self.assertEqual(TARGETS["piece_selector_stage"],0x15A1)
        self.assertEqual(TARGETS["piece_position_stage"],0x16E9)

if __name__=="__main__":
    unittest.main()
