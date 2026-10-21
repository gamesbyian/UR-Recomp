"""Bounded QA08 grayscale brightness-model ambiguity, not renderer acceptance.

These four observed source-class values are archived H25 research findings,
not independently verified same-epoch native effective-pixel observations.
Do not infer a unique shipping brightness coefficient or change the renderer.
"""
import unittest
from fractions import Fraction as F


def expand_5bit(value):
    if type(value) is not int or not 0 <= value < 32:
        raise ValueError("invalid 5-bit channel")
    return (value << 3) | (value >> 2)


def admissible_brightness_interval(observations):
    """All coefficients k satisfying floor(expand5(v)*k)==observed8."""
    if not isinstance(observations, dict) or not observations:
        raise ValueError("missing observations")
    lo, hi = F(0), None
    for v, y in observations.items():
        if type(v) is not int or type(y) is not int or not 1 <= v < 32 or not 0 <= y < 256:
            raise ValueError("invalid source observation")
        e = expand_5bit(v)
        lo = max(lo, F(y, e))
        upper = F(y + 1, e)
        hi = upper if hi is None else min(hi, upper)
    if hi is None or not lo < hi:
        raise ValueError("incompatible source observations")
    return lo, hi


class QA08BrightnessUnderdetermination(unittest.TestCase):
    SOURCE_H25_SAMPLES = {16: 123, 17: 130, 18: 138, 21: 161}

    def test_archived_four_classes_admit_multiple_models(self):
        lo, hi = admissible_brightness_interval(self.SOURCE_H25_SAMPLES)
        self.assertEqual((lo, hi), (F(69, 74), F(131, 140)))
        for k in (F(14, 15), F(187, 200)):
            with self.subTest(coefficient=str(k)):
                self.assertTrue(lo <= k < hi)
                for value, actual in self.SOURCE_H25_SAMPLES.items():
                    self.assertEqual(expand_5bit(value) * k // 1, actual)

    def test_unobserved_channel_22_is_a_discriminator(self):
        candidate_a, candidate_b = F(14, 15), F(187, 200)
        self.assertEqual(expand_5bit(22), 181)
        self.assertEqual((181 * candidate_a // 1, 181 * candidate_b // 1), (168, 169))
        self.assertNotIn(22, self.SOURCE_H25_SAMPLES)

    def test_interval_is_lower_closed_upper_open(self):
        lo, hi = admissible_brightness_interval(self.SOURCE_H25_SAMPLES)
        self.assertTrue(all(expand_5bit(v) * lo // 1 == y
                            for v, y in self.SOURCE_H25_SAMPLES.items()))
        self.assertFalse(all(expand_5bit(v) * hi // 1 == y
                             for v, y in self.SOURCE_H25_SAMPLES.items()))

    def test_invalid_or_conflicting_observations_fail_closed(self):
        for value in ({}, {0: 0}, {True: 0}, {32: 0}, {16: False},
                      {16: 260}, {16: 123, 17: 0}, None):
            with self.subTest(observations=value), self.assertRaises(ValueError):
                admissible_brightness_interval(value)


if __name__ == "__main__":
    unittest.main()
