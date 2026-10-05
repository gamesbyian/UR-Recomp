import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "probe", ROOT / "tools" / "probe_racer_hd_fallback_family.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class RacerHdFallbackFamilyProbeTests(unittest.TestCase):
    def test_target_is_the_measured_next_discriminator(self):
        self.assertEqual(MOD.TARGET_FRAMES, [1280, 1281, 1282, 1283, 1285, 1286])
        self.assertEqual(MOD.TARGET_STATE["p1_primary"], "0x0544")
        self.assertEqual(MOD.TARGET_STATE["p2_primary"], "0x0578")
        self.assertEqual(MOD.TARGET_STATE["p2_companion"], "0x0D63")
        self.assertEqual(MOD.TARGET_STATE["p2_companion_gate_word"], "0x0001")

    def test_same_player_probe_uses_fixed_stock_palettes(self):
        self.assertEqual(MOD.temporary_entry("p1")["palette_asset_id"], "0x06")
        self.assertEqual(MOD.temporary_entry("p2")["palette_asset_id"], "0x07")

    def test_approved_candidates_are_same_player_and_shipping_bound(self):
        registry = json.loads(
            (ROOT / "analysis/data/racer-hd-replacement-prototype.json").read_text()
        )
        for player in ("p1", "p2"):
            rows = MOD.approved_same_player_entries(registry, player)
            self.assertTrue(rows)
            self.assertTrue(all(row["player"] == player for row in rows))
            self.assertTrue(all(
                row["authored_candidate"]["shipping_approval_source"]
                for row in rows
            ))

    def test_alpha_mask_hash_ignores_rgb_but_not_occupancy(self):
        a = bytearray(64 * 64 * 4)
        b = bytearray(64 * 64 * 4)
        a[3] = 255
        b[0:4] = bytes((12, 34, 56, 255))
        self.assertEqual(MOD.alpha_mask_sha256(bytes(a)), MOD.alpha_mask_sha256(bytes(b)))
        b[7] = 255
        self.assertNotEqual(MOD.alpha_mask_sha256(bytes(a)), MOD.alpha_mask_sha256(bytes(b)))


if __name__ == "__main__":
    unittest.main()
