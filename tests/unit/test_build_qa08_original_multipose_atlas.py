"""Synthetic adversarial checks; never substitute these for original 2P evidence."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
import zipfile

from tools.art import build_qa08_original_multipose_atlas as atlas


def fake_zip(path: Path, corrupt=False, mirror_colour_mismatch=False):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for frame in atlas.FRAMES:
            for slot in atlas.SLOTS:
                raw = bytearray(atlas.WIDTH * atlas.HEIGHT * 4)
                x = 100 + (frame//16 % 3) + (2 if slot in (98,97) else 0)
                y = 52 if slot>=98 else 164
                pos = 4*(atlas.WIDTH*y+x)
                raw[pos:pos+4] = bytes((41 if mirror_colour_mismatch and frame==1872 and slot==97 else 40,40,40,255))
                digest=hashlib.sha256(raw).hexdigest()
                report={
                    "status": "passed",
                    "differing_original_rasters": [],
                    "identical_complete_original_342_rasters": 7,
                    "source_log_matches_pam": True,
                    "shared_full_frame_guest_ids": [1808,1824,1840,1856,1872,1888,2208],
                    "source":{
                        "guest_frame":frame, "slot":slot, "source_nonempty":True,
                        "source_sha256":digest,
                        "bbox":[x,y,x,y],
                        "top_opaque_source_pixels":int(y<112),
                        "bottom_opaque_source_pixels":int(y>=112),
                    }
                }
                source_name=(f"baldosa-ws342-obj-slots/"
                             f"ur-baldosa-ws342-obj-slot{slot}-frame{frame:06d}.pam")
                report_name=f"baldosa-evidence/ws342_obj_slot_{slot}_frame{frame}.json"
                if corrupt and frame==1872 and slot==98:
                    raw[pos] = 41
                z.writestr(source_name,atlas.header(atlas.WIDTH,atlas.HEIGHT)+bytes(raw))
                z.writestr(report_name,json.dumps(report))


class OriginalMultiPoseAtlas(unittest.TestCase):
    def test_consecutive_alpha_mask_jaccard(self):
        a={(10,20),(11,20),(11,21)}
        b={(20,30),(21,30),(22,30)}
        r=atlas.relative_jaccard(a,[10,20,11,21],b,[20,30,22,30])
        self.assertEqual(r["screen_translation_source_xy"],[10,10])
        self.assertEqual(r["shared_original_mask_pixels_after_bbox_alignment"],2)
        self.assertEqual(r["union_original_mask_pixels_after_bbox_alignment"],4)
        self.assertEqual(r["source_shape_Jaccard_after_bbox_origin_alignment"],0.5)

    def test_twelve_real_structured_source_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            archive=root/"sources.zip"
            fake_zip(archive)
            out=root/"atlas.html"
            data=atlas.build(archive,out)
            self.assertEqual(data["original_source_planes_authenticated"],12)
            self.assertEqual(len(data["source_planes"]),12)
            self.assertEqual(len(data["registered_alpha_shape_change"]),8)
            self.assertEqual(len(data["six_exact_cross_viewport_source_RGBA_aliases"]),6)
            self.assertTrue(all(x["bbox_registered_original_RGBA_exact"]
                for x in data["six_exact_cross_viewport_source_RGBA_aliases"].values()))
            self.assertFalse(data["procedural_HD_character_approved"])
            self.assertFalse(data["actual_final_BG_OBJ_winner_proven"])
            self.assertEqual(out.read_text().count('data:image/png;base64,'),12)
            self.assertIn('original native unicycles',out.read_text().lower())
            self.assertEqual(json.loads(out.with_suffix(".json").read_text()),data)

    def test_corrupted_binary_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"bad.zip"
            fake_zip(p,corrupt=True)
            with zipfile.ZipFile(p) as z:
                with self.assertRaisesRegex(ValueError,"SHA256 differs"):
                    atlas.source_sample(z,1872,98)

    def test_genuine_source_report_cannot_authorize_mismatched_2p_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            archive=root/"semantically-mismatched.zip"
            fake_zip(archive,mirror_colour_mismatch=True)
            with self.assertRaisesRegex(ValueError,"paired upper/lower"):
                atlas.build(archive,root/"out.html")

    def test_missing_alpha_or_report_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"valid.zip"
            fake_zip(p)
            with zipfile.ZipFile(p) as z:
                with self.assertRaises(KeyError):
                    atlas.source_sample(z,1856,98)
        with self.assertRaisesRegex(ValueError,"no real source pixels"):
            atlas.relative_jaccard(set(),[0,0,0,0],set(),[0,0,0,0])


if __name__=="__main__":
    unittest.main()
