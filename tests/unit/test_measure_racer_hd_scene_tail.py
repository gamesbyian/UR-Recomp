import unittest

from tools.measure_racer_hd_scene_tail import analyze_tail


def gate(frame, status, reason):
    return f"UR_RACER_HD_CENSUS frame={frame} phase=gate status={status} reason={reason}"


def present(frame, status, reason):
    return f"UR_RACER_HD_CENSUS frame={frame} phase=present status={status} reason={reason}"


def sample():
    return "\n".join([
        gate(100, "original", "disabled"), present(100, "original", "not-armed"),
        gate(101, "original", "p1-selection-or-art"), present(101, "original", "not-armed"),
        gate(102, "armed", "full-pair"), present(102, "hd", "full-pair"),
        gate(103, "armed", "full-pair"), present(103, "hd", "full-pair"),
        gate(104, "original", "p2-pair-gate"), present(104, "original", "not-armed"),
    ])


class HdSceneTailTests(unittest.TestCase):
    def test_excludes_boot_and_counts_actual_draws(self):
        result = analyze_tail(sample(), mode="vs", count=4)
        self.assertEqual(result["scene_mode"], "vs")
        self.assertEqual(result["frame_window"]["from"], 101)
        self.assertEqual(result["frame_window"]["to"], 104)
        m = result["measurement"]
        self.assertEqual(m["guest_frames_with_host_presents"], 4)
        self.assertEqual(m["hd_drawn_guest_frames"], 2)
        self.assertEqual(m["original_presented_guest_frames"], 2)
        self.assertEqual(m["draw_mode_switches"], 2)

    def test_accepts_all_stock_one_player_without_fake_hd_pass(self):
        log = "\n".join([
            gate(i, "original", "unsupported-geometry") + "\n" +
            present(i, "original", "not-armed")
            for i in range(40, 45)
        ])
        got = analyze_tail(log, mode="one-player", count=5)
        self.assertEqual(got["measurement"]["hd_drawn_guest_frames"], 0)
        self.assertEqual(got["measurement"]["original_presented_guest_frames"], 5)

    def test_malformed_cases_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "unsupported scene"):
            analyze_tail(sample(), mode="unknown", count=4)
        with self.assertRaisesRegex(ValueError, "tail length"):
            analyze_tail(sample(), mode="vs", count=0)
        with self.assertRaisesRegex(ValueError, "shorter"):
            analyze_tail(sample(), mode="vs", count=200)
        broken = "\n".join([
            gate(1, "original", "disabled"), present(1, "original", "not-armed"),
            gate(2, "armed", "full-pair"),
            gate(3, "original", "disabled"), present(3, "original", "not-armed"),
        ])
        with self.assertRaisesRegex(ValueError, "missing"):
            analyze_tail(broken, mode="vs", count=3)
        with self.assertRaisesRegex(ValueError, "no actual native"):
            analyze_tail(gate(1, "original", "disabled"), mode="vs", count=1)


if __name__ == "__main__":
    unittest.main()
