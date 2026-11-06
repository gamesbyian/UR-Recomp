"""One-GLB projected 2026 material support, not original game image fitting."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from tools.art.audit_source_spoke_blade_screen_support import (
    SCHEMA,ANGLES,RESOLUTIONS,HALF_SPAN,silhouette,analyze,
)


class SourceSpokeMaterialScreenSupportTests(unittest.TestCase):
    def test_fixed_camera_and_pixel_grid_contract(self):
        self.assertEqual(SCHEMA,"UR-ART4K-REAL-2026-GLB-BLADED-SPOKE-64PX-SUPPORT/1")
        self.assertEqual(ANGLES,(0,30,60,90))
        self.assertEqual(RESOLUTIONS,(64,128,256))
        self.assertEqual(HALF_SPAN,1.05)
        with tempfile.TemporaryDirectory() as root:
            fake=Path(root)/"not-the-source.glb"
            fake.write_bytes(b"not a real source GLB")
            with self.assertRaisesRegex(ValueError,"exact original authored"):
                analyze(fake)

    @unittest.skipUnless(importlib.util.find_spec("numpy") and
                         importlib.util.find_spec("trimesh") and
                         importlib.util.find_spec("PIL"),
                         "source-only projection requires optional Pillow/Trimesh/NumPy")
    def test_64px_triangle_source_material_area_bounded_and_orthogonal(self):
        import numpy as np
        import trimesh
        mesh=trimesh.Trimesh(vertices=np.asarray([
            [-.3,0,-.3],[.3,0,-.3],[0,0,.3],
        ]),faces=[[0,1,2]],process=False)
        image=silhouette(mesh,0,64)
        self.assertEqual(image.shape,(64,64))
        self.assertTrue(image.dtype==np.bool_)
        self.assertGreater(np.count_nonzero(image),10)
        for bad_angle in (-1,15,91,None,True):
            with self.assertRaises(ValueError):
                silhouette(mesh,bad_angle,64)
        for bad_size in (32,65,1000,True):
            with self.assertRaises(ValueError):
                silhouette(mesh,0,bad_size)
        with self.assertRaisesRegex(ValueError,"finite"):
            mesh.vertices=np.asarray([[float("nan"),0,0],[.3,0,0],[0,0,.3]])
            silhouette(mesh,0,64)


if __name__=="__main__":
    unittest.main()
