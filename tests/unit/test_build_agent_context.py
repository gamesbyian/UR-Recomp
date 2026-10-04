import unittest
from tools.build_agent_context import matching_blocks

class AgentContextTest(unittest.TestCase):
    def test_extracts_relevant_blocks_only(self):
        text = "alpha unrelated\n\nWidescreen accepted +32.\n\nother\n\nviewport next gate."
        self.assertEqual(matching_blocks(text, ["widescreen","viewport"]), ["Widescreen accepted +32.","viewport next gate."])

if __name__ == "__main__":
    unittest.main()
