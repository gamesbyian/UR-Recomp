import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "probe_visual",
    ROOT / "tools" / "probe_racer_hd_ranked_visual_context.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class RacerHdRankedVisualContextProbeTests(unittest.TestCase):
    def test_composition_guard_translation_preserves_full_runtime_state(self):
        composition = {
            "p1_primary": "0x0239",
            "p2_primary": "0x0546",
            "p1_companion": "0x0000",
            "p2_companion": "0x0EB2",
            "p1_selector": 0,
            "p2_selector": 0,
            "p1_gate": "0x0000",
            "p2_gate": "0x0001",
        }
        guards = MOD.composition_guards(composition)
        self.assertEqual(guards["p1_primary"], "0x0239")
        self.assertEqual(guards["p2_companion"], "0x0EB2")
        self.assertEqual(guards["p2_companion_gate_word"], "0x0001")

    def test_local_match_ignores_peer_only_for_visual_grouping(self):
        target = {
            "player": "p2",
            "semantic_frame_id": "0x0546",
            "companion": "0x0EB2",
            "selector": 0,
            "gate": "0x0001",
        }
        a = {
            "p1_primary": "0x0239", "p2_primary": "0x0546",
            "p1_companion": "0x0000", "p2_companion": "0x0EB2",
            "p1_selector": 0, "p2_selector": 0,
            "p1_gate": "0x0000", "p2_gate": "0x0001",
        }
        b = dict(a)
        b["p1_primary"] = "0x04B9"
        self.assertTrue(MOD.local_matches(a, target))
        self.assertTrue(MOD.local_matches(b, target))
        b["p2_companion"] = "0x0EB3"
        self.assertFalse(MOD.local_matches(b, target))


if __name__ == "__main__":
    unittest.main()
