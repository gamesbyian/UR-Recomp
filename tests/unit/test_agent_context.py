import json
import unittest
from pathlib import Path

from tools.build_agent_context import matching_json_entries

ROOT = Path(__file__).resolve().parents[2]


class AgentContextStructuredAuthorityTest(unittest.TestCase):
    def test_json_extraction_keeps_matching_object_context(self):
        data = {
            "settings": [
                {"id": "audio", "runtime_status": "integrated"},
                {
                    "id": "widescreen",
                    "menu_symbol": "UR_MODERN_OPTIONS_WIDESCREEN",
                    "runtime_status": "integrated",
                },
            ]
        }
        entries = matching_json_entries(data, ["Options", "setting"])
        rendered = "\n".join(entries)
        self.assertIn("settings[1]", rendered)
        self.assertIn("widescreen", rendered)
        self.assertNotIn('\"id\":\"audio\"', rendered)

    def test_configured_json_authorities_produce_context(self):
        config = json.loads((ROOT / "analysis/agent-context-lanes.json").read_text())
        checked = []
        for lane in ("modern-product", "racer-hd"):
            keywords = config["lanes"][lane]["keywords"]
            for authority in config["lanes"][lane]["authorities"]:
                path = ROOT / authority
                if path.suffix != ".json":
                    continue
                checked.append((lane, authority))
                entries = matching_json_entries(json.loads(path.read_text()), keywords)
                self.assertTrue(
                    entries,
                    f"{lane} structured authority produced no extracted context: {authority}",
                )
        self.assertTrue(checked)


if __name__ == "__main__":
    unittest.main()
