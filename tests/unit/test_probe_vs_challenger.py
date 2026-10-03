import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import probe_vs_challenger as probe  # noqa: E402


def o(menu, texts, column=0x06):
    return {"menu": menu, "column": column, "row": 0, "p1_rider": 0, "p2_rider": 1, "texts": texts}


GOOD = {
    "vsc-result": o(0xF9, ["DRAGSTER", "COMPLETE", "MIKE", "0:28.76", "ANDREW", "NO TIME"]),
    "vsc-champions": o(0xD3, ["VS CHAMPIONS"]),
    "vsc-pick-challenger": o(0x3F, ["PICK CHALLENGER"]),
    "vsc-pick-after-p1": o(0x3F, ["PICK CHALLENGER"]),
    "vsc-track-choice": o(0x5A, probe.TRACK_CHOICES),
    "vsc-next": o(0x16, ["NOW PLAYING"]),
}


class VsChallengerTests(unittest.TestCase):
    def test_good_flow_passes(self) -> None:
        self.assertTrue(all(probe.evaluate(GOOD).values()))

    def test_p1_moving_the_cursor_fails_inert_check(self) -> None:
        bad = dict(GOOD)
        bad["vsc-pick-after-p1"] = o(0x3F, ["PICK CHALLENGER"], column=0x07)
        self.assertFalse(probe.evaluate(bad)["p1_inert_on_pick_challenger"])

    def test_branch_input_replaces_final_confirm(self) -> None:
        out = probe.branch_input(["# c", "4460:2:000:100", "4620:2:000:100"], 2).splitlines()
        self.assertEqual(out, ["4460:2:000:100", "4600:2:000:020", "4630:2:000:020", "4680:2:000:100"])

    def test_branches(self) -> None:
        ok = {1: o(0x16, ["NOW PLAYING"]), 2: o(0x91, ["PICK TRACK"]), 3: o(0x6D, ["PICK TOUR"]), 4: o(0xD7, ["1P"])}
        self.assertTrue(all(probe.evaluate_branches(ok).values()))
        ok[4] = o(0x16, ["NOW PLAYING"])
        self.assertFalse(probe.evaluate_branches(ok)["track_choice_quit_reaches_0xD7"])

    def test_draw(self) -> None:
        draw = {"vsd-result": o(0xF9, ["COMPLETE", "NO TIME", "NO TIME"]),
                "vsd-rematch": o(0xB7, ["REMATCH"]), "vsd-after": o(0x16, ["NOW PLAYING"])}
        self.assertTrue(all(probe.evaluate_draw(draw).values()))


if __name__ == "__main__":
    unittest.main()
