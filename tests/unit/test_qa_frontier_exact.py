"""Synthetic-only exact frontier census contracts; no gameplay correctness credit."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa_frontier_exact as e
import qa_frontier_coverage as h


def tokens(start: int, count: int, seed: int = 50000000) -> dict:
    return {f"{n:024x}": (seed + i // 3, "balanced", 0)
            for i, n in enumerate(range(start, start + count))}


class ExactFrontierTests(unittest.TestCase):
    def test_lossless_exact_10000_cohort_and_overlap(self):
        a = tokens(0, 30000)
        encoded = e.encode_run(a)
        self.assertEqual(e._parse(encoded, False), a)
        first, gain = e.make_record(None, a, 38171000000, 10000)
        self.assertEqual(gain["exact_new_unique_fingerprints"], 30000)
        b = tokens(20000, 20000, seed=50012000)
        duplicate, update = e.make_record(first, b, 38171000001, 10000)
        self.assertEqual(update["exact_new_unique_fingerprints"], 10000)
        self.assertEqual(update["exact_post_unique_fingerprints"], 40000)
        seen = e.validate_record(duplicate)
        self.assertEqual(seen[f"{20001:024x}"][0], 38171000000)
        third, repeated = e.make_record(duplicate, b, 38171000002, 10000)
        self.assertEqual(repeated["exact_new_unique_fingerprints"], 0)
        self.assertEqual(third["exact_unique_observed_fingerprints"], 40000)

    def test_count_is_exact_only_for_normalized_fingerprints(self):
        report_tokens = tokens(0, 100, seed=50000000)
        report = {
            "semantic_epoch": h.EPOCH,
            "semantic_bins_observed": 100,
            "semantic_hll_b64": h.encode(h.observe(set(report_tokens))),
            "semantic_exact_witnesses_b64": e.encode_run(report_tokens),
        }
        self.assertEqual(e.observed_report(report, 50000000, 100, 4), report_tokens)
        for alteration in (
            {"semantic_bins_observed": 101},
            {"semantic_hll_b64": h.encode(h.empty())},
            {"semantic_epoch": "different-normalization"},
            {"semantic_exact_witnesses_b64": e.encode_run(
                {f"{0:024x}": (50015000, "balanced", 0)})},
        ):
            with self.subTest(alteration=alteration), self.assertRaises(ValueError):
                e.observed_report({**report, **alteration}, 50000000, 100, 4)

    def test_reject_tampering_and_unsupported_witness(self):
        first, _ = e.make_record(None, tokens(0, 100), 38171000000, 100)
        for key, value in (
            ("record_sha256", "0" * 64),
            ("exact_unique_observed_fingerprints", 200),
            ("release_gate_credit", 1),
            ("original_native_parity_claimed", True),
            ("semantic_epoch", "new-unreviewed-epoch"),
            ("witnesses_b64", "invalid"),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                e.validate_record({**first, key: value})
        with self.assertRaises(ValueError):
            e.encode_run({f"{0:024x}": (50000000, "unknown-arm", 0)})
        with self.assertRaises(ValueError):
            e.encode_run({f"{0:024x}": (50000000, "balanced", 40)})
        with self.assertRaises(ValueError):
            e._parse(e._pack(b"bad-length"), True)
        with self.assertRaises(ValueError):
            e._parse(e._pack(b"\x00" * (e.RUN_WIDTH * 2)), False)

    def test_prior_legacy_hll_is_not_converted_to_exact(self):
        record, _ = e.make_record(None, tokens(4, 30), 38171000000, 10)
        self.assertTrue(record["legacy_sketch_campaigns_excluded"])
        self.assertEqual(record["exact_unique_observed_fingerprints"], 30)
        self.assertFalse(record["original_native_parity_claimed"])


if __name__ == "__main__":
    unittest.main()
