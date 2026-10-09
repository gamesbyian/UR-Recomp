import json
from pathlib import Path
import unittest


EVIDENCE = (
    Path(__file__).resolve().parents[2]
    / "analysis/generated/racer-hd-native-live-race-window-2026-10-09.json"
)


class RacerHdNativeLiveWindowEvidenceTests(unittest.TestCase):
    def test_exact_guest_denominator_and_bursts(self):
        report = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        window = report["analyzed_window"]
        lo, hi = window["guest_frames_inclusive"]
        self.assertEqual(hi - lo + 1, window["guest_frames_observed"])
        self.assertEqual(window["guest_frames_presented"], window["guest_frames_observed"])
        self.assertEqual(window["missing_guest_frames"], 0)
        ranges = window["hd_run_ranges"]
        self.assertEqual(len(ranges), window["hd_run_count"])
        hd = set()
        for first, last in ranges:
            self.assertLessEqual(first, last)
            self.assertGreaterEqual(first, lo)
            self.assertLessEqual(last, hi)
            self.assertFalse(hd.intersection(range(first, last + 1)))
            hd.update(range(first, last + 1))
        self.assertEqual(len(hd), window["hd_full_pair_drawn_frames"])
        self.assertEqual(
            sum(first == last for first, last in ranges),
            window["one_frame_hd_runs"],
        )
        self.assertEqual(
            max(last - first + 1 for first, last in ranges),
            window["highest_hd_run_length"],
        )
        self.assertEqual(
            window["original_presented_frames"] + window["hd_full_pair_drawn_frames"],
            window["guest_frames_presented"],
        )
        self.assertEqual(
            window["original_presented_frames"],
            sum(window["original_gate_reasons"].values()),
        )
        self.assertEqual(window["hd_player_frames"], 2 * len(hd))
        self.assertEqual(window["total_player_frames"], 2 * window["guest_frames_presented"])
        self.assertAlmostEqual(
            window["hd_fraction"],
            window["hd_player_frames"] / window["total_player_frames"],
        )
        entry = sum(f not in hd and f + 1 in hd for f in range(lo, hi))
        exit_ = sum(f in hd and f + 1 not in hd for f in range(lo, hi))
        self.assertEqual(entry, window["original_to_hd_edges"])
        self.assertEqual(exit_, window["hd_to_original_edges"])
        self.assertEqual(entry + exit_, window["render_mode_switches"])
        stock_runs = []
        for frame in range(lo, hi + 1):
            if frame in hd:
                continue
            if not stock_runs or frame != stock_runs[-1][-1] + 1:
                stock_runs.append([frame])
            else:
                stock_runs[-1].append(frame)
        longest = max(stock_runs, key=len)
        self.assertEqual(
            longest, list(range(*(
                window["longest_original_run"][0],
                window["longest_original_run"][1] + 1,
            )))
        )
        self.assertEqual(len(longest), window["longest_original_run_frames"])

    def test_native_and_reference_routes_not_conflated(self):
        report = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(report["provenance"]["input"],
                         "tests/input/two-player-first-race.input")
        self.assertEqual(report["provenance"]["artifact_id"], 11591057403)
        self.assertEqual(len(report["provenance"]["member_log_sha256"]), 64)
        self.assertNotEqual(
            report["analyzed_window"]["guest_frames_observed"],
            2641,
        )
        self.assertTrue(any(
            "Not comparable" in caveat for caveat in report["exclusions"]
        ))


if __name__ == "__main__":
    unittest.main()
