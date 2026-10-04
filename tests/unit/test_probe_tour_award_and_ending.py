import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import probe_tour_award_and_ending as probe  # noqa: E402

W = probe.WIN_CUT
S = probe.SCENE_FRAME


def s(menu=0x99, tiers=0, flag=0, medals=None, fb="a"):
    return {"menu": menu, "tiers": [tiers] * 16, "tier_backup": [0] * 16, "cheat_flag": flag,
            "medals": medals or [0] * 9, "tour_flags": [[0] * 5 for _ in range(9)], "fb_sha1": fb}


def medal(row, value):
    m = [0] * 9
    m[row] = value
    return m


def good() -> dict:
    obs = {"cheat": s(0xD7, tiers=3, flag=1), "cheat_control": s(0xD7), "cheat_reboot": s(0xD7),
           "bronze": {W: s(medals=medal(0, 1)), S: s(medals=medal(0, 1))}}
    for row, name in enumerate(probe.TOURS[:8]):
        obs[f"gold_{name}"] = {W: s(medals=medal(row, 3)), S: s(medals=medal(row, 3), fb=name),
                               S + 300: s(0x6D, medals=medal(row, 3))}
    obs["ending"] = {W: s(medals=medal(8, 3)), S: s(medals=medal(8, 3), fb="news"), S + 1400: s(0x5B, medals=medal(8, 3))}
    obs["ending_cheat"] = {W: s(flag=1, medals=medal(8, 3)), S: s(flag=1, medals=medal(8, 3), fb="cheat"),
                           S + 100: s(0x5B, flag=1, medals=medal(8, 3))}
    return obs


class TourAwardEndingTests(unittest.TestCase):
    def test_expected_observations_pass(self) -> None:
        checks = probe.evaluate(good())
        self.assertTrue(all(checks.values()), {k: v for k, v in checks.items() if not v})

    def test_missing_ending_fails(self) -> None:
        obs = good()
        obs["ending"][S + 1400]["menu"] = 0x84
        self.assertFalse(probe.evaluate(obs)["ending_reaches_ending_menu"])

    def test_cheat_not_restored_fails(self) -> None:
        obs = good()
        obs["cheat_reboot"] = s(0xD7, tiers=3, flag=1)
        self.assertFalse(probe.evaluate(obs)["next_boot_restores_tiers"])

    def test_shared_gold_scene_fails(self) -> None:
        obs = good()
        obs["gold_jumper"][S]["fb_sha1"] = "crawler"
        self.assertFalse(probe.evaluate(obs)["gold_scenes_differ_per_tour"])

    def test_scripts_seed_the_right_rows(self) -> None:
        self.assertIn("spoke 1076 01010101", probe.award_script(probe.AWARD_SCENARIOS["bronze"]))
        jumper = probe.award_script(probe.AWARD_SCENARIOS["gold_jumper"])
        self.assertIn("spoke 107A 01010101", jumper)
        self.assertIn("spoke 06AC 02", jumper)
        self.assertIn("pokefor CE 090001 200", jumper)
        ending = probe.award_script(probe.AWARD_SCENARIOS["ending"])
        self.assertIn("spoke 109D 01010101", ending)
        self.assertIn("pokefor CE 2C0008 200", ending)


if __name__ == "__main__":
    unittest.main()
