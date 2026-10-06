import unittest
from unittest.mock import patch

from tools.check_racer_hd_temporal_coherence import (
    alpha_mask,
    build_report,
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

    def test_single_player_motion_review_sequence(self):
        rid = "p1-only"
        registry = {
            "family": "test",
            "entries": [{
                "representation_id": rid,
                "semantic_frame_id": "0x04B9",
                "player": "p1",
                "registration": {
                    "semantic_anchors": {"wheel_contact_x2_y2": [1, 0]}
                },
                "authored_candidate": {"kind": "test"},
            }],
            "motion_review_sequences": {
                "p1-static": {
                    "window_start": 10,
                    "window_end": 11,
                    "players": ["p1"],
                    "sampling": "test",
                    "frames": [
                        {"frame": 10, "p1_representation_id": rid},
                        {"frame": 11, "p1_representation_id": rid},
                    ],
                    "acceptance": {
                        "dynamic_transition_ratio_min": 0.25,
                        "dynamic_transition_ratio_max": 4.0,
                    },
                }
            },
        }
        stock = bytearray(64 * 64 * 4)
        stock[3] = 255
        authored = bytearray(256 * 256 * 4)
        authored[(((0 * 4 + 2) * 256) + (0 * 4 + 2)) * 4 + 3] = 255
        with patch(
            "tools.check_racer_hd_temporal_coherence.build_stock_rgba",
            return_value=bytes(stock),
        ), patch(
            "tools.check_racer_hd_temporal_coherence.authored_candidate_rgba_for_entry",
            return_value=(bytes(authored), "generator", "sampler"),
        ):
            report = build_report(b"", registry, "p1-static")
        self.assertEqual(report["players"], ["p1"])
        self.assertEqual(set(report["sequences"]), {"p1"})
        self.assertTrue(all(report["validation"].values()))

    def test_xor_requires_equal_masks(self):
        with self.assertRaises(ValueError):
            xor_count([0], [0, 1])


if __name__ == "__main__":
    unittest.main()
