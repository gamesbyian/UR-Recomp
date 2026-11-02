"""ROM-free authenticated original chroma connectivity and axis controls."""
import unittest
from tools.art.audit_original_racer_chroma_components import (
    source_chroma_pixels,connected_components,centroid_axis,painted_components,
)


def synthetic(colour, include_isolated=False):
    data=bytearray(64*64*4)
    for y in range(10,24):
        x=20
        k=4*(y*64+x)
        data[k:k+4]=bytes((*colour,255))
    if include_isolated:
        k=4*(23*64+50)
        data[k:k+4]=bytes((*colour,255))
    return bytes(data)


class OriginalPaintedComponentTests(unittest.TestCase):
    def test_detached_pixel_changes_original_axis_not_largest_region(self):
        a=painted_components(synthetic((180,15,12),True),"p1")
        b=painted_components(synthetic((180,15,12),False),"p1")
        self.assertEqual(a["eight_neighbour_component_pixel_counts"],[14,1])
        self.assertEqual(b["eight_neighbour_component_pixel_counts"],[14])
        self.assertEqual(a["largest_component_axis_degrees"],0.)
        self.assertEqual(b["largest_component_axis_degrees"],0.)
        self.assertNotEqual(a["original_whole_chroma_axis_degrees"],0.)
        self.assertFalse(a["source_2d_chroma_is_one_physical_3d_part"])

    def test_blue_p2_and_red_p1_are_palette_independent_rules(self):
        blue=synthetic((12,17,190))
        self.assertEqual(len(source_chroma_pixels(blue,"p2")),14)
        self.assertEqual(centroid_axis(source_chroma_pixels(blue,"p2")),0.)
        with self.assertRaisesRegex(ValueError,"too small"):
            source_chroma_pixels(blue,"p1")
        with self.assertRaises(ValueError):
            source_chroma_pixels(blue,"p3")

    def test_diagonal_connectivity_is_explicit(self):
        points={(10,10),(11,11),(12,12)}
        self.assertEqual([len(g) for g in connected_components(points,diagonal=False)],
                         [1,1,1])
        self.assertEqual([len(g) for g in connected_components(points,diagonal=True)],[3])
        with self.assertRaises(ValueError):
            connected_components({(64,2)},diagonal=True)
        with self.assertRaises(ValueError):
            connected_components(set(),diagonal=True)

    def test_invalid_source_rgba_and_fractional_alpha_fail_closed(self):
        source=bytearray(synthetic((200,12,20)))
        source[3]=128
        with self.assertRaisesRegex(ValueError,"binary alpha"):
            source_chroma_pixels(bytes(source),"p1")
        with self.assertRaises(ValueError):
            painted_components(b"invalid","p1")
        with self.assertRaises(ValueError):
            centroid_axis({(20,10),(20,11)})


if __name__=="__main__":
    unittest.main()
