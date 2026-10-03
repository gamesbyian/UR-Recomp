import unittest

from tools.prototype_racer_hd_replacement import (
    alpha_bounds,
    alpha_contact_anchor_x2_y2,
    flip_rgba,
    lock_alpha,
    nearest_rgba,
    object_flip_pivot_x2_y2,
    scale2x_rgba,
    scaled_bounds,
    guards_match,
    load_entry,
    select_representation,
    transform_anchor_x2_y2,
)


def px(r, g, b, a=255):
    return bytes((r, g, b, a))


class RacerHdReplacementPrototypeTests(unittest.TestCase):
    def test_scale2x_preserves_flat_field(self):
        red = px(255, 0, 0)
        src = red * 4
        self.assertEqual(scale2x_rgba(src, 2, 2), red * 16)

    def test_alpha_lock_preserves_scaled_stock_extent(self):
        t = px(0, 0, 0, 0)
        w = px(255, 255, 255)
        src = b"".join([
            t, w, t,
            w, w, t,
            t, t, t,
        ])
        candidate = scale2x_rgba(src, 3, 3)
        reference = nearest_rgba(src, 3, 3, 2)
        out = lock_alpha(candidate, reference)
        self.assertEqual(len(out), 6 * 6 * 4)
        self.assertEqual(alpha_bounds(out, 6, 6), scaled_bounds(alpha_bounds(src, 3, 3), 2))

    def test_anchor_geometry_is_exact_and_flip_stable(self):
        t = px(0, 0, 0, 0)
        w = px(255, 255, 255)
        src = b"".join([
            t, t, t, t,
            t, w, w, t,
            w, w, w, t,
        ])
        self.assertEqual(object_flip_pivot_x2_y2(4, 3), [3, 2])
        contact = alpha_contact_anchor_x2_y2(src, 4, 3)
        self.assertEqual(contact, [2, 4])
        self.assertEqual(transform_anchor_x2_y2(contact, 4, 3, True, False), [4, 4])
        self.assertEqual(transform_anchor_x2_y2(contact, 4, 3, False, True), [2, 0])
        self.assertEqual(transform_anchor_x2_y2(contact, 4, 3, True, True), [4, 0])

    def test_selector_fails_closed_to_original(self):
        registry = {
            "entries": [{
                "semantic_frame_id": "0x0541",
                "composition_guards": {
                    "p1_primary": "0x0541",
                    "p1_selector": 0,
                },
            }]
        }
        exact = {"p1_primary": "0x0541", "p1_selector": 0}
        mismatch = {"p1_primary": "0x0542", "p1_selector": 0}
        self.assertTrue(guards_match(registry["entries"][0]["composition_guards"], exact))
        self.assertEqual(
            select_representation(registry, "0x0541", exact, True)[0],
            "remastered_candidate",
        )
        self.assertEqual(
            select_representation(registry, "0x0541", exact, False)[0],
            "original",
        )
        self.assertEqual(
            select_representation(registry, "0x0541", mismatch, True)[0],
            "original",
        )
        self.assertEqual(
            select_representation(registry, "0x0999", exact, True)[0],
            "original",
        )

    def test_duplicate_semantic_ids_select_by_full_composition(self):
        registry = {
            "entries": [
                {
                    "semantic_frame_id": "0x057E",
                    "representation_id": "state-a",
                    "composition_guards": {"p1_primary": "0x057E", "p2_primary": "0x0543"},
                },
                {
                    "semantic_frame_id": "0x057E",
                    "representation_id": "state-b",
                    "composition_guards": {"p1_primary": "0x057E", "p2_primary": "0x0544"},
                },
            ]
        }
        state_a = {"p1_primary": "0x057E", "p2_primary": "0x0543"}
        state_b = {"p1_primary": "0x057E", "p2_primary": "0x0544"}
        selected_a = select_representation(registry, "0x057E", state_a, True)
        selected_b = select_representation(registry, "0x057E", state_b, True)
        self.assertEqual(selected_a[0], "remastered_candidate")
        self.assertEqual(selected_a[1]["representation_id"], "state-a")
        self.assertEqual(selected_b[1]["representation_id"], "state-b")
        self.assertEqual(
            load_entry(registry, "0x057E", representation_id="state-b")["representation_id"],
            "state-b",
        )
        with self.assertRaises(ValueError):
            load_entry(registry, "0x057E")

    def test_nearest_and_flip_are_deterministic(self):
        a, b, c, d = px(1, 0, 0), px(2, 0, 0), px(3, 0, 0), px(4, 0, 0)
        src = a + b + c + d
        up = nearest_rgba(src, 2, 2, 2)
        self.assertEqual(len(up), 4 * 4 * 4)
        flipped_twice = flip_rgba(flip_rgba(up, 4, 4, True, False), 4, 4, True, False)
        self.assertEqual(flipped_twice, up)


if __name__ == "__main__":
    unittest.main()
