import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import probe_tier_opponents as probe  # noqa: E402

NAMES = ["mike"] + ["x"] * 16 + ["bronsen", "silvia", "goldwyn", "anti-uni"]


def obs(index, name, label):
    return {"tier_label": label, "card_opponent_name": name, "card_texts": [], "p2_rider_index": index,
            "in_race": 1, "p2_palette_matches_asset": True, "p2_palette_asset": f"0x{6 + index:02X}"}


class TierOpponentTests(unittest.TestCase):
    def test_seeded_sram_keeps_checksum_valid(self) -> None:
        clean = bytearray(0x2000)
        clean[0x5E8] = 0x10
        c = probe.checksum(clean)
        clean[0x73C], clean[0x73D] = c & 0xFF, c >> 8
        out = probe.seeded(bytes(clean), 2)
        self.assertEqual(out[probe.MEDAL_CELL], 2)
        self.assertEqual(probe.checksum(out), out[0x73C] | out[0x73D] << 8)
        self.assertEqual(probe.checksum(out), (0x10 + 2) & 0xFFFF)  # 069C is the low byte of an even word

    def test_summarize_rule(self) -> None:
        good = {0: obs(17, "BRONSEN", "BRONZE"), 1: obs(18, "SILVIA", "SILVER"), 2: obs(19, "GOLDWYN", "GOLD")}
        self.assertTrue(probe.summarize(good, NAMES)["all_checks_pass"])
        bad = dict(good)
        bad[1] = obs(17, "BRONSEN", "SILVER")
        report = probe.summarize(bad, NAMES)
        self.assertFalse(report["all_checks_pass"])
        self.assertFalse(report["checks"]["medal1_opponent_index_18"])


if __name__ == "__main__":
    unittest.main()
