import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "probe_state", ROOT / "tools" / "probe_racer_hd_state_reuse.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class GenericRacerHdStateReuseProbeTests(unittest.TestCase):
    def test_target_entry_keeps_exact_state_and_player_palette(self):
        state = {
            "p1_primary": "0x0545",
            "p2_primary": "0x057C",
            "p1_companion": "0x0000",
            "p2_companion": "0x0C27",
            "p1_selector": 0,
            "p2_selector": 0,
            "p1_companion_gate_word": "0x0000",
            "p2_companion_gate_word": "0x0001",
        }
        p1 = MOD.target_entry("p1", state)
        p2 = MOD.target_entry("p2", state)
        self.assertEqual(p1["composition_guards"], state)
        self.assertEqual(p2["composition_guards"], state)
        self.assertEqual(p1["palette_asset_id"], "0x06")
        self.assertEqual(p2["palette_asset_id"], "0x07")

    def test_approved_catalog_requires_shipping_source(self):
        registry = {
            "entries": [
                {"representation_id": "a", "authored_candidate": {"shipping_approval_source": "x"}},
                {"representation_id": "b", "authored_candidate": {}},
                {"representation_id": "c"},
            ]
        }
        self.assertEqual(
            [x["representation_id"] for x in MOD.approved_entries(registry)],
            ["a"],
        )


if __name__ == "__main__":
    unittest.main()
