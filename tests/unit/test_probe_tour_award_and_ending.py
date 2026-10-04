import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import probe_tour_award_and_ending as probe  # noqa: E402


def s(menu=0x99, tiers=0, flag=0, crawler=0, hunter=0, fb="a", cflags=0, hflags=0):
    return {"menu": menu, "tiers": [tiers] * 16, "tier_backup": [0] * 16, "cheat_flag": flag,
            "crawler": crawler, "hunter": hunter, "crawler_flags": [cflags] * 5, "hunter_flags": [hflags] * 5,
            "fb_sha1": fb}


W = probe.WIN_CUT


def good() -> dict:
    return {
        "cheat": s(0xD7, tiers=3, flag=1), "cheat_control": s(0xD7), "cheat_reboot": s(0xD7),
        "bronze": {W: s(crawler=1)},
        "gold": {W: s(crawler=3), W + 452: s(0x6D, crawler=3)},
        "ending": {W: s(hunter=3), W + 152: s(hunter=3, fb="news"), W + 1552: s(0x5B, hunter=3)},
        "ending_cheat": {W: s(hunter=3, flag=1), W + 152: s(hunter=3, flag=1, fb="cheat"), W + 252: s(0x5B, hunter=3, flag=1)},
    }


class TourAwardEndingTests(unittest.TestCase):
    def test_expected_observations_pass(self) -> None:
        checks = probe.evaluate(good())
        self.assertTrue(all(checks.values()), checks)

    def test_missing_ending_fails(self) -> None:
        obs = good()
        obs["ending"][W + 1552]["menu"] = 0x84
        self.assertFalse(probe.evaluate(obs)["ending_reaches_ending_menu"])

    def test_cheat_not_restored_fails(self) -> None:
        obs = good()
        obs["cheat_reboot"] = s(0xD7, tiers=3, flag=1)
        self.assertFalse(probe.evaluate(obs)["next_boot_restores_tiers"])

    def test_same_ending_page_fails(self) -> None:
        obs = good()
        obs["ending_cheat"][W + 152]["fb_sha1"] = "news"
        self.assertFalse(probe.evaluate(obs)["cheat_flag_changes_ending_page"])

    def test_award_script_seeds_hunter_row(self) -> None:
        script = probe.award_script(probe.AWARD_SCENARIOS["ending"])
        self.assertIn("spoke 109D 01010101", script)
        self.assertIn("pokefor CE 2C0008 200", script)
        self.assertIn("spoke 1076 01010101", probe.award_script(probe.AWARD_SCENARIOS["bronze"]))


if __name__ == "__main__":
    unittest.main()
