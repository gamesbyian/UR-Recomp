import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import probe_challenge_generation as probe  # noqa: E402
import probe_tier_opponents as tier  # noqa: E402


def obs(label: str, opponent: int, name: str) -> dict:
    return {
        "tier_label": label,
        "p2_rider_index": opponent,
        "card_opponent_name": name,
        "in_race": 1,
    }


class ChallengeGenerationProbeTests(unittest.TestCase):
    def test_classification(self) -> None:
        control = obs("BRONZE", 17, "BRONSEN")
        self.assertEqual(
            probe.classify(control, obs("GOLD", 19, "GOLDWYN")),
            "full-generation-seam")
        self.assertEqual(
            probe.classify(control, obs("GOLD", 17, "BRONSEN")),
            "label-only-seam")
        self.assertEqual(
            probe.classify(control, obs("BRONZE", 17, "BRONSEN")),
            "no-effect")
        self.assertEqual(
            probe.classify(control, obs("SILVER", 19, "GOLDWYN")),
            "mixed-or-unexpected")

    def test_integrity_summary(self) -> None:
        sram = bytearray(0x2000)
        sram[tier.MEDAL_CELL] = 0
        sram[probe.SNAPSHOT] = 2
        value = tier.checksum(sram)
        sram[tier.CHECKSUM_AT] = value & 0xFF
        sram[tier.CHECKSUM_AT + 1] = value >> 8

        report = probe.summarize(
            obs("BRONZE", 17, "BRONSEN"),
            obs("GOLD", 19, "GOLDWYN"),
            bytes(sram))
        self.assertEqual(report["classification"], "full-generation-seam")
        self.assertTrue(report["candidate_is_full_generation_seam"])
        self.assertTrue(report["all_integrity_checks_pass"])


if __name__ == "__main__":
    unittest.main()
