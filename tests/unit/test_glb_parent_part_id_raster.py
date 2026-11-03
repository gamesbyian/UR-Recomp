"""Synthetic, ROM-free colour-independent parent ID and Z-buffer contracts."""
import json
import unittest
from pathlib import Path
from tools.art.glb_parent_part_id_raster import raster_part_ids,PART_IDS

CAMERA={"schema":"UR-RACER-FIXED-ORTHOGRAPHIC-CAMERA/1",
        "source_pixel_aspect":"7:6","camera_calibration_status":"provisional",
        "right_world":[1,0,0],"up_world":[0,0,1],"origin_world":[0,0,0],
        "logical_pixels_per_model_unit_vertical":7,"source_anchor_x2_y2":[32,32]}

def triangle(part,x,y=0,colour=None):
    return {"part":part,"vertices":[(x,y,0),(x+.35,y,0),(x,y,.35)],
            "faces":[(0,1,2)],"colour_ignored":colour}

class GLBParentIDs(unittest.TestCase):
    def test_depth_and_material_colours_are_independent(self):
        meshes=[triangle("tire",0,colour="red"),
                triangle("rim_and_hub",0,y=-.4,colour="blue"),
                triangle("fork_and_frame",.6),triangle("pedals",1.2),
                triangle("saddle",1.8)]
        a=raster_part_ids(meshes,CAMERA)
        self.assertEqual(a["id_plane_256"][66*256+66],PART_IDS["rim_and_hub"])
        meshes[0]["colour_ignored"]="pink";meshes[1]["colour_ignored"]="yellow"
        b=raster_part_ids(meshes,CAMERA)
        self.assertEqual(a,b)
    def test_equal_depth_different_parents_fail(self):
        meshes=[triangle("tire",0),triangle("rim_and_hub",0),
                triangle("fork_and_frame",.6),triangle("pedals",1.2),triangle("saddle",1.8)]
        with self.assertRaisesRegex(ValueError,"indistinguishable"):
            raster_part_ids(meshes,CAMERA)
    def test_missing_parts_camera_or_clipping_fail(self):
        meshes=[triangle(x,i*.5) for i,x in enumerate(PART_IDS)]
        with self.assertRaisesRegex(ValueError,"five"):
            raster_part_ids(meshes[:-1],CAMERA)
        with self.assertRaisesRegex(ValueError,"provisional"):
            raster_part_ids(meshes,{**CAMERA,"camera_calibration_status":"source-calibrated"})
        with self.assertRaisesRegex(ValueError,"clip"):
            raster_part_ids(meshes[:-1]+[triangle("saddle",200)],CAMERA)


    def test_nearest_third_parent_wins_regardless_of_mesh_order(self):
        # The first two parents are within epsilon, but a third is clearly
        # closer than both. An early tie must not preempt the final winner.
        meshes=[triangle("tire",0),
                triangle("rim_and_hub",0,y=-.9e-7),
                triangle("fork_and_frame",0,y=-2e-7),
                triangle("pedals",1.2),triangle("saddle",1.8)]
        first=raster_part_ids(meshes,CAMERA)
        reverse=raster_part_ids(list(reversed(meshes)),CAMERA)
        self.assertEqual(first,reverse)
        self.assertEqual(first["id_plane_256"][66*256+66],
                         PART_IDS["fork_and_frame"])

    def test_sub_epsilon_same_parent_depth_cannot_hide_cross_parent_tie(self):
        # Same true nearest depths in both permutations. The second tire
        # fragment was previously discarded by an epsilon-filtered winner.
        meshes=[triangle("tire",0),triangle("tire",0,y=-.9e-7),
                triangle("rim_and_hub",0,y=-1.8e-7),
                triangle("fork_and_frame",.6),
                triangle("pedals",1.2),triangle("saddle",1.8)]
        for order in (meshes,list(reversed(meshes))):
            with self.assertRaisesRegex(ValueError,"indistinguishable"):
                raster_part_ids(order,CAMERA)


    def test_frozen_five_glb_receipt_digest_fields_are_complete(self):
        path=(Path(__file__).resolve().parents[2] /
              "analysis/data/racer-source-index-and-model-part-evidence-20261102.json")
        report=json.loads(path.read_text(encoding="utf-8"))
        poses=report["experimental_model"]["poses"]
        self.assertEqual(set(poses),{"upright","pedal","wheelie","stunt","bank"})
        for pose,receipt in poses.items():
            for key in ("glb_sha256","part_id_64_sha256","part_id_256_sha256"):
                with self.subTest(pose=pose,key=key):
                    self.assertRegex(receipt[key],r"\A[0-9a-f]{64}\Z")
        # Actual artifact #13063969312, independently re-rastered at 256px.
        self.assertEqual(poses["upright"]["part_id_256_sha256"],
                         "0b2b1e2979bf08fb145d59ed6090c1db6099075c7b91b8494badd3bb905cc1b5")

if __name__=="__main__":
    unittest.main()
