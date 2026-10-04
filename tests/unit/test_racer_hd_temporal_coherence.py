import unittest

from tools.check_racer_hd_temporal_coherence import (
    alpha_mask,
    evaluate_transition,
    logical_center_alpha_mask,
    xor_count,
)


def px(a):
    return bytes((1, 2, 3, a))


class RacerHdTemporalCoherenceTests(unittest.TestCase):
    def test_alpha_mask_and_xor_count(self):
        a = px(0) + px(255) + px(0) + px(255)
        b = px(0) + px(0) + px(255) + px(255)
        self.assertEqual(alpha_mask(a), [0, 1, 0, 1])
        self.assertEqual(alpha_mask(b), [0, 0, 1, 1])
        self.assertEqual(xor_count(alpha_mask(a), alpha_mask(b)), 2)

    def test_logical_center_alpha_mask_samples_4x_centres(self):
        rgba = bytearray(8 * 8 * 4)
        # W/H are 64 in production; use a full-size authored buffer and set
        # one logical centre to keep this test aligned with the real sampler.
        rgba = bytearray(256 * 256 * 4)
        index = (((3 * 4 + 2) * 256) + (5 * 4 + 2)) * 4 + 3
        rgba[index] = 255
        mask = logical_center_alpha_mask(bytes(rgba))
        self.assertEqual(sum(mask), 1)
        self.assertEqual(mask[3 * 64 + 5], 1)

    def test_transition_gate_preserves_static_and_bounds_dynamic_ratio(self):
        base = {
            "frame": 1,
            "representation_id": "a",
            "_stock_mask": [0, 1, 0, 1],
            "_authored_mask": [0, 1, 0, 1],
            "stock_contact_x2_y2": [10, 20],
            "authored_contact_x2_y2": [10, 20],
        }
        still = {
            **base,
            "frame": 2,
            "representation_id": "b",
        }
        static = evaluate_transition(base, still, 0.75, 2.25)
        self.assertEqual(static["transition_class"], "static")
        self.assertTrue(static["static_edge_preserved"])

        moving = {
            **base,
            "frame": 3,
            "representation_id": "c",
            "_stock_mask": [1, 1, 0, 1],
            "_authored_mask": [1, 1, 1, 1],
            "stock_contact_x2_y2": [12, 20],
            "authored_contact_x2_y2": [12, 20],
        }
        dynamic = evaluate_transition(base, moving, 0.75, 2.25)
        self.assertEqual(dynamic["transition_class"], "dynamic")
        self.assertTrue(dynamic["dynamic_edge_preserved"])
        self.assertTrue(dynamic["transition_ratio_within_bounds"])
        self.assertEqual(
            dynamic["stock_contact_delta_x2_y2"],
            dynamic["authored_contact_delta_x2_y2"],
        )

    def test_xor_requires_equal_masks(self):
        with self.assertRaises(ValueError):
            xor_count([0], [0, 1])


if __name__ == "__main__":
    unittest.main()
