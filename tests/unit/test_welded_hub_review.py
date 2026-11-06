"""Mechanical acceptance only for a REVIEW-ONLY 2026 housing alternative."""
import math
import tempfile
import unittest
from pathlib import Path

from tools.art.welded_hub_review import (
    EXPECTED_NODES, FACE_COUNT, HUB_NODE, RING_COUNT, VERTEX_COUNT,
    check_closed_shell, welded_housing, make_preview,
)


def source_cylinder_vertices():
    return [(0.086 * math.cos(2 * math.pi * k / 50), y,
             0.086 * math.sin(2 * math.pi * k / 50))
            for y in (-.21, .21) for k in range(50)]


class WeldedHubReviewTests(unittest.TestCase):
    def test_one_closed_volume_has_no_pretend_source_recovery(self):
        vertices, faces = welded_housing(source_cylinder_vertices())
        self.assertEqual((RING_COUNT, len(vertices), len(faces)),
                         (58, VERTEX_COUNT, FACE_COUNT))
        self.assertAlmostEqual(check_closed_shell(vertices, faces),
                               0.0749600518095, places=7)
        self.assertLess(max(math.hypot(x, z) for x, y, z in vertices), .5)
        self.assertAlmostEqual(min(x for x, y, z in vertices), -.30)
        self.assertAlmostEqual(max(x for x, y, z in vertices), .22)
        self.assertAlmostEqual(min(z for x, y, z in vertices), -.37)
        self.assertAlmostEqual(max(z for x, y, z in vertices), .27)
        self.assertAlmostEqual(min(y for x, y, z in vertices), -.21)
        self.assertAlmostEqual(max(y for x, y, z in vertices), .38)
        self.assertEqual((vertices, faces),
                         welded_housing(source_cylinder_vertices()))

    def test_corrupted_source_and_bad_topology_fail(self):
        source = source_cylinder_vertices()
        candidates = (source[:-1],
                      source[:-1] + [(0, 0, 0)],
                      [(x, y + .01, z) for x, y, z in source],
                      [(x * 1.5, y, z) for x, y, z in source])
        for bad in candidates:
            with self.subTest(length=len(bad)), self.assertRaises(ValueError):
                welded_housing(bad)
        vertices, faces = welded_housing(source)
        with self.assertRaises(ValueError):
            check_closed_shell(vertices, faces[:-1])
        with self.assertRaises(ValueError):
            check_closed_shell(vertices, [tuple(reversed(f)) for f in faces])
        with self.assertRaises(ValueError):
            check_closed_shell(vertices, [faces[0]] + faces[1:-1])
        altered = list(vertices)
        altered[0] = altered[1]
        with self.assertRaises(ValueError):
            check_closed_shell(altered, faces)

    def test_canonical_part_graph_has_five_parents_and_sixteen_materials(self):
        self.assertEqual(len(EXPECTED_NODES), 16)
        self.assertIn(HUB_NODE, EXPECTED_NODES)

    def test_optional_real_export_fails_closed_on_unrelated_input(self):
        try:
            import trimesh
        except ImportError:
            self.skipTest('trimesh optional: real GLB acceptance is a separate run')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unrelated = root / 'unrelated.glb'
            unrelated.write_bytes(trimesh.Scene(trimesh.creation.box()).export(file_type='glb'))
            with self.assertRaises(ValueError):
                make_preview(unrelated, root / 'rejected.glb')
            self.assertFalse((root / 'rejected.glb').exists())


if __name__ == '__main__':
    unittest.main()
