"""QA-08: independent integrity check for the archived moving-scene eligibility census.

A frame admitted by *both* semantic selectors is only an upper bound on
visible HD replacement. This regression tests the actual archived run ranges
and the provenance-bearing JSON, not a collection of isolated pose fixtures.
"""

from collections import Counter
import json
from pathlib import Path
import unittest


EVIDENCE = (
    Path(__file__).resolve().parents[2]
    / "analysis/generated/racer-hd-pair-temporal-eligibility-2026-10-08.json"
)


class RacerHdPairTemporalEvidenceTests(unittest.TestCase):
    def test_archived_episode_ranges_and_eligibility_edges_are_consistent(self):
        report = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        measure = report["measurement"]
        lo, hi = report["source"]["frame_range"]
        observed = list(range(lo, hi + 1))
        self.assertEqual(len(observed), measure["observed_guest_frames"])
        self.assertEqual(len(observed) - 1, measure["consecutive_frame_pairs"])

        ranges = report["eligible_episode_inclusive_ranges"]
        episodes = []
        eligible = set()
        for start, end in ranges:
            self.assertGreaterEqual(start, lo)
            self.assertLessEqual(end, hi)
            self.assertLessEqual(start, end)
            if episodes:
                self.assertGreater(start, episodes[-1][-1] + 1)
            frames = list(range(start, end + 1))
            self.assertFalse(eligible.intersection(frames))
            eligible.update(frames)
            episodes.append(frames)

        histogram = dict(sorted(Counter(map(len, episodes)).items()))
        self.assertEqual(
            {str(length): count for length, count in histogram.items()},
            measure["eligible_episode_length_histogram"]
        )
        self.assertEqual(len(episodes), measure["eligible_episode_count"])
        self.assertEqual(sum(map(len, episodes)), measure["registered_pair_eligible_guest_frames"])
        self.assertEqual(max(map(len, episodes)), measure["eligible_longest_episode_frames"])
        self.assertEqual(histogram[1], measure["one_frame_eligible_episodes"])

        stock_runs = []
        for frame in observed:
            if frame in eligible:
                continue
            if not stock_runs or frame != stock_runs[-1][-1] + 1:
                stock_runs.append([frame])
            else:
                stock_runs[-1].append(frame)
        longest_stock = max(stock_runs, key=len)
        self.assertEqual(
            len(longest_stock),
            measure["longest_consecutive_pair_ineligible_run_frames"]
        )
        self.assertEqual(
            [longest_stock[0], longest_stock[-1]],
            measure["longest_consecutive_pair_ineligible_run_inclusive_range"]
        )
        for start, end in measure["other_long_pair_ineligible_ranges"]:
            self.assertTrue(all(frame not in eligible for frame in range(start, end + 1)))
        for key in ("first_441_guest_frame_window", "remaining_2200_guest_frame_window"):
            window = measure[key]
            lo_window, hi_window = window["range"]
            self.assertEqual(
                sum(lo_window <= frame <= hi_window for frame in eligible),
                window["registered_pair_eligible_frames"]
            )

        edges = list(zip(observed, observed[1:]))
        entry = sum(a not in eligible and b in eligible for a, b in edges)
        exit_ = sum(a in eligible and b not in eligible for a, b in edges)
        self.assertEqual(entry, measure["adjacent_stock_to_eligible_edges"])
        self.assertEqual(exit_, measure["adjacent_eligible_to_stock_edges"])
        self.assertEqual(entry + exit_, measure["adjacent_eligibility_switches"])
        self.assertEqual(
            measure["registered_pair_eligible_player_frame_upper_bound"],
            2 * len(eligible)
        )
        self.assertEqual(
            measure["original_fallback_player_frames_lower_bound"],
            measure["observed_player_frames"] - 2 * len(eligible)
        )
        self.assertAlmostEqual(
            measure["eligible_fraction_upper_bound"],
            2 * len(eligible) / measure["observed_player_frames"]
        )

    def test_provenance_does_not_overclaim_native_pixel_fidelity(self):
        report = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertIn("not live native", report["classification"])
        self.assertEqual(report["source"]["artifact_id"], 11539984901)
        self.assertEqual(
            len(report["source"]["source_member_sha256"]), 64
        )
        self.assertTrue(any(
            "not evidence" in note for note in report["exclusions"]
        ))


if __name__ == "__main__":
    unittest.main()
