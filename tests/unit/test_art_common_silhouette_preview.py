"""Art authoring at 32/64px: only ONE measured crop for an entire pose family."""
import unittest
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.art.common_silhouette_preview import common_pose_crop


class LockedCameraReadablePreviews(unittest.TestCase):
    def test_family_shared_crop_covers_all_extrema_without_pose_autofit(self):
        families=[[30,105,85,250], [90,95,180,260], [50,32,135,200],
                  [150,80,220,210], [70,70,180,260]]
        crop=common_pose_crop(families,320,320)
        self.assertEqual(crop[2]-crop[0],crop[3]-crop[1])
        for x0,y0,x1,y1 in families:
            self.assertLessEqual(crop[0],x0)
            self.assertLessEqual(crop[1],y0)
            self.assertGreaterEqual(crop[2],x1)
            self.assertGreaterEqual(crop[3],y1)
        # The selected shared source frame is smaller than the entire camera;
        # a 32px preview thus cannot be an unreadable whole-viewport shrink.
        self.assertLess(crop[2]-crop[0],320)
        self.assertEqual(crop, common_pose_crop(families[::-1],320,320))

    def test_edge_shift_stays_inside_camera_for_all_poses(self):
        family=[[1,50,60,120],[1,80,50,130]]
        crop=common_pose_crop(family,256,224,0.08)
        self.assertEqual(crop[0],0)
        self.assertTrue(0<=crop[1]<crop[3]<=224)
        self.assertLessEqual(crop[0],1)
        self.assertGreaterEqual(crop[2],60)

    def test_fail_closed_missing_bad_or_incomplete_extrema(self):
        cases=[([],320,320),
               ([[0,0,0,5]],320,320),
               ([[3,3,300,300]],320,300),
               ([[0,0,21,20],[-1,0,25,25]],320,320),
               ([[0.1,2,15,15]],320,320),
               ([[0,0,20]],320,320),
               ([['0',0,20,20]],320,320),
               ([[1,1,20,20]],True,320)]
        for boxes,w,h in cases:
            with self.subTest(boxes=boxes),self.assertRaises(ValueError):
                common_pose_crop(boxes,w,h)
        for invalid in (float("nan"),-0.1,0.4,True,0):
            with self.subTest(margin=invalid),self.assertRaises(ValueError):
                common_pose_crop([[10,10,20,20]],320,320,invalid)

    def test_real_reviewers_use_common_crop_but_never_publish_art(self):
        static=(ROOT/"tools/art/render_shared_unicycle_review.py").read_text()
        motion=(ROOT/"tools/art/render_shared_unicycle_motion.py").read_text()
        self.assertIn("common_pose_crop([item[\"silhouette_bbox\"] for item in view_rows]",static)
        self.assertIn("model_rgb.crop(crop).resize((px,px)",static)
        self.assertIn('"normal_size_previews_per_pose_autofit": False',static)
        self.assertIn("common_pose_crop([row[\"silhouette_bbox\"] for row in actual]",motion)
        self.assertIn('source_im.convert("RGB").crop(sprite_crop)',motion)
        self.assertIn('"normal_size_preview_per_frame_autofit": False',motion)
        self.assertIn('"shipping_art_approved": False',motion)
        self.assertIn('"original_native_RGB5_PPU_equivalence":False',static)


if __name__=="__main__":
    unittest.main()
