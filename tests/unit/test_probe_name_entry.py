import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import probe_name_entry as probe  # noqa: E402


class NameEntryPlanTests(unittest.TestCase):
    def test_cells(self) -> None:
        self.assertEqual(probe.cell_for("A"), (0, 0))
        self.assertEqual(probe.cell_for("T"), (1, 6))
        self.assertEqual(probe.cell_for("Z"), (1, 12))

    def test_plan_matches_hand_route_for_sonic(self) -> None:
        moves = [l for l in probe.plan_moves("SONIC") if l.startswith("press")]
        # From T: S is one left; O four left; N one left; I up and right 8; C left 6; OK down 3 right 10.
        self.assertEqual(moves.count("press a 2"), 6)
        self.assertEqual(moves[:2], ["press left 1", "press a 2"])
        self.assertEqual(moves[-1], "press a 2")
        self.assertEqual(sum(1 for m in moves if m == "press down 1"), 3)

    def test_rejects_non_letters(self) -> None:
        with self.assertRaises(ValueError):
            probe.cell_for("1")


if __name__ == "__main__":
    unittest.main()
