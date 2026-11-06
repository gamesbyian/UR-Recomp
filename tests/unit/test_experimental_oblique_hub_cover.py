"""Source-locked single 2026 hub cover prototype, not original 1994 reconstruction."""
import importlib.util
import json
import os
from pathlib import Path
import unittest

from tools.art.experimental_oblique_hub_cover import (
    authored_oblique_hub_cover,counterspun_hub_cover_vertices,
    SOURCE_MATERIAL,CURRENT_2026_SOURCE_GLB_SHA256,
    ORIGINAL_SOURCE_VERTEX_COUNT,ORIGINAL_SOURCE_FACE_COUNT,
    NEW_HUB_COVER_VERTICES,NEW_HUB_COVER_FACES,
)
from tools.art.audit_source_hub_cover_volume import analyze,SCHEMA

ROOT=Path(__file__).resolve().parents[2]
SCORE=ROOT/"analysis/data/racer-art4k-2026-print-exposed-hub-cover-proposal-20261105.json"


class ExperimentalOriginalPrintHubCoverTests(unittest.TestCase):
    def test_one_frozen_closed_plate_faces_geometry_and_source_restrictions(self):
        v,f=authored_oblique_hub_cover()
        self.assertEqual(len(v),16)
        self.assertEqual(len(f),28)
        self.assertEqual(SOURCE_MATERIAL,"rim_and_hub__material_4")
        self.assertEqual((ORIGINAL_SOURCE_VERTEX_COUNT,ORIGINAL_SOURCE_FACE_COUNT),(100,196))
        self.assertEqual((NEW_HUB_COVER_VERTICES,NEW_HUB_COVER_FACES),(16,28))
        self.assertEqual(CURRENT_2026_SOURCE_GLB_SHA256,
                         "634aa0280ec1a8a322c34d1598680e854980f317965b3a848a2cf6b240c50c08")
        self.assertEqual(len(set(v)),16)
        self.assertTrue(all(0<=i<16 for row in f for i in row))
        self.assertEqual(len(set(tuple(sorted(row)) for row in f)),28)
        self.assertAlmostEqual(min(x[0] for x in v),-.30)
        self.assertAlmostEqual(max(x[0] for x in v),.22)
        self.assertAlmostEqual(min(x[1] for x in v),.18)
        self.assertAlmostEqual(max(x[1] for x in v),.38)
        self.assertAlmostEqual(min(x[2] for x in v),-.37)
        self.assertAlmostEqual(max(x[2] for x in v),.27)

    def test_2026_counterspin_matches_existing_wheel_parent_inverse_exactly(self):
        import math
        original,_=authored_oblique_hub_cover()
        self.assertEqual(counterspun_hub_cover_vertices(0),original)
        self.assertEqual(counterspun_hub_cover_vertices(0.),original)
        for degrees in (-360,-225,-90,-15,15,24,90,180,345,360):
            child=counterspun_hub_cover_vertices(degrees)
            a=math.radians(degrees)
            c,q=math.cos(a),math.sin(a)
            for (x,y,z),(xx,yy,zz) in zip(original,child):
                # Existing 2026 wheel transform Ry(-phase) exactly cancels
                # the proposed axle-fixed cover inverse local rotation.
                self.assertAlmostEqual(c*xx-q*zz,x,places=12)
                self.assertAlmostEqual(q*xx+c*zz,z,places=12)
                self.assertAlmostEqual(yy,y,places=12)
        self.assertNotEqual(counterspun_hub_cover_vertices(24),original)
        for bad in (True,None,3j,float("nan"),float("inf"),361,-361,"45"):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                counterspun_hub_cover_vertices(bad)

    def test_frozen_original_model_only_numeric_receipt_never_claims_1994_3d(self):
        score=json.loads(SCORE.read_text(encoding="utf-8"))
        self.assertEqual(score["schema"],SCHEMA)
        self.assertEqual(score["original_2026_source_upright_glb_sha256"],
                         CURRENT_2026_SOURCE_GLB_SHA256)
        self.assertEqual(score["source_original_print_visible_hub_face_2d_area_scan_px2"],
                         35973.5)
        self.assertEqual(score["new_total_dark_hub_material_vertices"],116)
        self.assertEqual(score["new_total_dark_hub_material_triangles"],224)
        self.assertEqual(score["prototype_closed_components_in_one_material"],2)
        self.assertAlmostEqual(score["source_dark_hub_material_original_volume_2026_units3"],
                               0.009733130,8)
        self.assertAlmostEqual(score["source_dark_hub_material_proposed_volume_2026_units3"],
                               0.075653130,8)
        self.assertFalse(score["prototype_is_boolean_fused_single_manifold"])
        for name in ("same_1994_model_or_artist_camera_proven",
                     "original_1994_physical_hub_width_depth_or_shape_recovered",
                     "original_1994_material_identity_recovered",
                     "owner_character_likeness_approved","shipping_art_approved"):
            self.assertIs(score[name],False,name)

    @unittest.skipUnless(importlib.util.find_spec("trimesh"),
                         "optional exact-source original 2026 GLB test requires trimesh")
    def test_proposal_closed_casing_solid_has_correct_volume(self):
        import trimesh
        m=trimesh.Trimesh(*authored_oblique_hub_cover(),process=False)
        self.assertTrue(m.is_watertight)
        self.assertAlmostEqual(m.volume,0.06592,6)
        for phase in (0,15,24,90,180,345):
            transformed=trimesh.Trimesh(counterspun_hub_cover_vertices(phase),
                                       m.faces.copy(),process=False)
            self.assertTrue(transformed.is_watertight)
            self.assertAlmostEqual(transformed.volume,m.volume,places=10)

    @unittest.skipUnless(importlib.util.find_spec("numpy") and
                         importlib.util.find_spec("trimesh"),
                         "original source GLB model requires numpy/trimesh")
    def test_actual_2026_source_glb_reproduces_same_hypothesis_if_supplied(self):
        name=os.getenv("UR_ART4K_AUTHORED_UPRIGHT_GLB")
        if not name:
            self.skipTest("real original 2026 GLB supplied separately; no duplicate CI export")
        observed=analyze(Path(name))
        self.assertEqual(observed,json.loads(SCORE.read_text(encoding="utf-8")))


if __name__=="__main__":
    unittest.main()
