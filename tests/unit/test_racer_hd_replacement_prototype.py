import unittest

from tools.prototype_racer_hd_replacement import (
    alpha_bounds,
    flip_rgba,
    nearest_rgba,
    scale2x_rgba,
    scaled_bounds,
)


def px(r, g, b, a=255):
    return bytes((r, g, b, a))


class RacerHdReplacementPrototypeTests(unittest.TestCase):
    def test_scale2x_preserves_flat_field(self):
        red = px(255, 0, 0)
        src = red * 4
        self.assertEqual(scale2x_rgba(src, 2, 2), red * 16)

    def test_scale2x_smooths_corner_without_changing_extent(self):
        t = px(0, 0, 0, 0)
        w = px(255, 255, 255)
        src = b"".join([
            t, w, t,
            w, w, t,
            t, t, t,
        ])
        out = scale2x_rgba(src, 3, 3)
        self.assertEqual(len(out), 6 * 6 * 4)
        self.assertEqual(alpha_bounds(out, 6, 6), scaled_bounds(alpha_bounds(src, 3, 3), 2))

    def test_nearest_and_flip_are_deterministic(self):
        a, b, c, d = px(1, 0, 0), px(2, 0, 0), px(3, 0, 0), px(4, 0, 0)
        src = a + b + c + d
        up = nearest_rgba(src, 2, 2, 2)
        self.assertEqual(len(up), 4 * 4 * 4)
        flipped_twice = flip_rgba(flip_rgba(up, 4, 4, True, False), 4, 4, True, False)
        self.assertEqual(flipped_twice, up)


if __name__ == "__main__":
    unittest.main()
