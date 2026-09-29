#!/usr/bin/env python3
"""Regression tests for course-layout plane statistics."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from analyze_course_layout_planes import entropy, stats


class CourseLayoutPlaneTests(unittest.TestCase):
    def test_uniform_region(self):
        data = bytes([7]) * 1024
        s = stats(data)
        self.assertEqual(s["length"], 1024)
        self.assertEqual(s["distinct_bytes"], 1)
        self.assertEqual(s["zero_fraction"], 0.0)
        self.assertEqual(s["entropy_bits_per_byte"], 0.0)
        self.assertEqual(s["fraction_lt_16"], 1.0)
        self.assertEqual(s["fraction_lt_64"], 1.0)

    def test_full_byte_alphabet_has_eight_bit_entropy(self):
        data = bytes(range(256)) * 4
        self.assertAlmostEqual(entropy(data), 8.0)
        s = stats(data)
        self.assertEqual(s["distinct_bytes"], 256)
        self.assertEqual(s["zero_fraction"], round(4 / 1024, 6))
        self.assertAlmostEqual(s["fraction_lt_64"], 0.25)

    def test_sparse_index_like_region(self):
        data = bytes([0] * 768 + [1] * 128 + [2] * 64 + [3] * 64)
        s = stats(data)
        self.assertEqual(s["distinct_bytes"], 4)
        self.assertEqual(s["zero_fraction"], 0.75)
        self.assertLess(s["entropy_bits_per_byte"], 2.0)

    def test_shape_aware_neighbor_continuity(self):
        # Four identical horizontal rows: horizontal neighbors always match;
        # vertical neighbors always match as well.
        data = bytes([1] * 256) * 4
        s = stats(data, 256, 4)
        self.assertEqual(s["horizontal_equal_fraction"], 1.0)
        self.assertEqual(s["vertical_equal_fraction"], 1.0)
        self.assertEqual(s["horizontal_mean_abs_delta"], 0.0)
        self.assertEqual(s["vertical_mean_abs_delta"], 0.0)

    def test_neighbor_metric_rejects_wrong_shape(self):
        data = bytes(range(16))
        s = stats(data, 5, 3)
        self.assertIsNone(s["horizontal_equal_fraction"])
        self.assertIsNone(s["vertical_equal_fraction"])


if __name__ == "__main__":
    unittest.main()
