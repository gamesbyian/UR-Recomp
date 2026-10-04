import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import probe_menu_sfx_ids as probe  # noqa: E402


def ring(head, entries):
    w = bytearray(0x3000)
    w[probe.RING_HEAD] = head
    for i, word in entries.items():
        w[probe.RING_LO + i], w[probe.RING_HI + i] = word & 0xFF, word >> 8
    return bytes(w)


class MenuSfxTests(unittest.TestCase):
    def test_new_commands_follow_the_ring_and_wrap(self) -> None:
        before = ring(14, {})
        after = ring(2, {14: 0x087F, 15: 0x0203, 0: 0x084F, 1: 0x0202})
        self.assertEqual(probe.new_commands(before, after), ["087F", "0203", "084F", "0202"])
        self.assertEqual(probe.classify(["087F", "0203", "084F", "0202"]), [3, 2])

    def test_evaluate_expected_contract(self) -> None:
        e = lambda *ids: {"sfx": list(ids)}
        obs = {"main_cursor_down": e(3), "tour_cursor_down": e(3, 3), "main_confirm_1p_slide": e(2),
               "tour_confirm": e(2), "rider_confirm": e(4, 2), "track_back_to_tour": e(1),
               "tour_back_to_rider": e(1), "rider_back_to_main": e(1), "editor_cursor_right": e(3),
               "editor_type_letter": e(6), "editor_delete": e(6), "forbidden_ok": e(4), "valid_ok": e(4, 1)}
        self.assertTrue(all(probe.evaluate(obs).values()))
        obs["main_cursor_down"] = e()
        self.assertFalse(probe.evaluate(obs)["cursor_moves_play_sfx_3"])

    def test_carrier_steps_are_marked(self) -> None:
        events = probe.editor_events("ZED", "valid")
        self.assertTrue(events[0][0].endswith(probe.CARRIER))
        self.assertEqual(events[1][1][:2], ["press a 2", "wait 20"])


if __name__ == "__main__":
    unittest.main()
