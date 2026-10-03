import unittest

from tools.check_racer_hd_temporal_coherence import alpha_mask, xor_count


def px(a):
    return bytes((1, 2, 3, a))


class RacerHdTemporalCoherenceTests(unittest.TestCase):
    def test_alpha_mask_and_xor_count(self):
        a = px(0) + px(255) + px(0) + px(255)
        b = px(0) + px(0) + px(255) + px(255)
        self.assertEqual(alpha_mask(a), [0, 1, 0, 1])
        self.assertEqual(alpha_mask(b), [0, 0, 1, 1])
        self.assertEqual(xor_count(alpha_mask(a), alpha_mask(b)), 2)

    def test_xor_requires_equal_masks(self):
        with self.assertRaises(ValueError):
            xor_count([0], [0, 1])


if __name__ == "__main__":
    unittest.main()
