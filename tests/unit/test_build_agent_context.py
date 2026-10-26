import unittest
from tools.build_agent_context import matching_blocks

class AgentContextTest(unittest.TestCase):
    def test_extracts_relevant_blocks_only(self):
        text = "alpha unrelated\n\nWidescreen accepted +32.\n\nother\n\nviewport next gate."
        self.assertEqual(matching_blocks(text, ["widescreen","viewport"]), ["Widescreen accepted +32.","viewport next gate."])


    def test_release_lane_uses_exact_checkout_and_does_not_grant_credit(self):
        from unittest.mock import patch
        from tools import build_agent_context as module
        with patch.object(module, "git_text", return_value="e" * 40):
            rendered = "\n".join(module.release_brief_section("release-qa"))
        self.assertIn("Source versus nominated candidate: MISMATCH", rendered)
        self.assertIn("QA-01:", rendered)
        self.assertIn("QA-12:", rendered)
        self.assertIn("No independent evidence was checked", rendered)

    def test_no_git_head_does_not_misstate_source_match(self):
        from unittest.mock import patch
        from tools import build_agent_context as module
        with patch.object(module, "git_text", return_value="unavailable"):
            rendered = "\n".join(module.release_brief_section("ci"))
        self.assertIn("unknown (HEAD unavailable)", rendered)
        self.assertIn("QA-12:", rendered)
        self.assertNotIn("QA-01:", rendered)

    def test_corrupt_ledger_fails_closed_in_context(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from tools import build_agent_context as module
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "docs"
            d.mkdir()
            (d / "RELEASE-QUALITY-LEDGER.json").write_text("{}")
            with patch.object(module, "ROOT", Path(tmp)):
                lines = module.release_brief_section("release-qa")
        self.assertIn("navigation unavailable", "\n".join(lines))
        self.assertNotIn("passed; ", "\n".join(lines))


if __name__ == "__main__":
    unittest.main()
