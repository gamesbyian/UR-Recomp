"""ROM-free adversarial tests for exact original OBJ colour/orientation diagnostics."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.art.audit_original_postcountdown_obj_compositing import (
    BONUS_RED_5BIT, compare_opaque_pixels, analyse,
)
from tools.art.audit_original_postcountdown_obj_screen import TICKS


def synthetic_obj(pixels:dict[tuple[int,int],tuple[int,int,int]]) -> dict:
    size=64
    plane=bytearray(size*size)
    alpha=bytearray(size*size)
    rgba=bytearray(size*size*4)
    for (x,y),rgb in pixels.items():
        index=y*size+x
        plane[index]=1
        alpha[index]=1
        rgba[4*index:4*index+4]=bytes((*rgb,255))
    return {"size":size,"plane":bytes(plane),"alpha_mask":bytes(alpha),
            "rgba":bytes(rgba),"opaque_count":len(pixels)}


def screen_for(placements:dict[tuple[int,int],tuple[int,int,int]]) -> bytes:
    result=bytearray(256*239*3)
    for (x,y),rgb in placements.items():
        result[3*(y*256+x):3*(y*256+x)+3]=bytes(rgb)
    return bytes(result)


class OriginalCompositingTests(unittest.TestCase):
    def test_exact_source_red_5bit_addition_and_rgb_correspondence(self):
        # R5=9 -> 22: RGB red 74 -> 181. R5=3 -> 16:
        # 24 -> 132. R5=20 -> saturated 31: 165 -> 255.
        obj=synthetic_obj({
            (0,0):(74,74,74),
            (1,0):(24,24,24),
            (2,0):(165,165,165),
            (3,0):(255,0,0),
        })
        screen=screen_for({
            (20,20):(181,74,74),
            (21,20):(132,24,24),
            (22,20):(255,165,165),
            (23,20):(255,0,0),
        })
        result=compare_opaque_pixels(obj,screen,x=20,y=20,horizontal_mirror=False)
        self.assertEqual((result["source_opaque_pixels"],result["direct_exact_RGB"],
                          result["red_5bit_plus_13_RGB"],result["unaccounted_RGB"]),
                         (4,1,3,0))
        self.assertEqual(result["source_chromatic_pixels"],1)
        self.assertEqual(result["source_chromatic_pixels_accounted"],1)
        self.assertEqual(BONUS_RED_5BIT,13)
        for addition in (12,14):
            wrong=compare_opaque_pixels(obj,screen,x=20,y=20,
                                        horizontal_mirror=False,red_addend=addition)
            self.assertGreater(wrong["unaccounted_RGB"],0)

    def test_horizontal_mirror_diagnostic_preserves_source_and_is_not_auto_applied(self):
        obj=synthetic_obj({(2,6):(255,0,0),(8,6):(74,74,74)})
        before=obj["rgba"]
        screen=screen_for({(30+61,40+6):(255,0,0),
                           (30+55,40+6):(181,74,74)})
        flipped=compare_opaque_pixels(obj,screen,x=30,y=40,horizontal_mirror=True)
        self.assertEqual((flipped["direct_exact_RGB"],
                          flipped["red_5bit_plus_13_RGB"],
                          flipped["unaccounted_RGB"]),(1,1,0))
        original=compare_opaque_pixels(obj,screen,x=30,y=40,horizontal_mirror=False)
        self.assertEqual(original["unaccounted_RGB"],2)
        shift=compare_opaque_pixels(obj,screen,x=31,y=40,horizontal_mirror=True)
        self.assertGreater(shift["unaccounted_RGB"],0)
        self.assertEqual(obj["rgba"],before)

    def test_refuses_unverified_screen_geometry_and_corrupt_original_alpha(self):
        obj=synthetic_obj({(0,0):(74,74,74)})
        display=screen_for({})
        for kw in ({"x":True,"y":20,"horizontal_mirror":False},
                   {"x":193,"y":20,"horizontal_mirror":False},
                   {"x":0,"y":176,"horizontal_mirror":False},
                   {"x":0,"y":0,"horizontal_mirror":1},
                   {"x":0,"y":0,"horizontal_mirror":False,"red_addend":32},
                   {"x":0,"y":0,"horizontal_mirror":False,"red_addend":True}):
            with self.subTest(kw=kw),self.assertRaisesRegex(ValueError,"bounded"):
                compare_opaque_pixels(obj,display,**kw)
        bad={**obj,"alpha_mask":bytes(64*64)}
        with self.assertRaisesRegex(ValueError,"inconsistent"):
            compare_opaque_pixels(bad,display,x=0,y=0,horizontal_mirror=False)
        wrong_channel=synthetic_obj({(0,0):(75,74,74)})
        with self.assertRaisesRegex(ValueError,"five-bit"):
            compare_opaque_pixels(wrong_channel,display,x=0,y=0,horizontal_mirror=False)

    def test_untrusted_frames_cannot_be_promoted_to_original_source(self):
        for frames in ([],[{}],[{"tick":1601}]*5):
            with self.subTest(frames=frames),self.assertRaisesRegex(
                    ValueError,"consecutive"):
                analyse(frames)

    def test_frozen_real_five_frame_receipt_and_negative_gates(self):
        path=Path(__file__).resolve().parents[2] / (
            "analysis/data/racer-original-postcountdown-obj-flip-red-overlay-20261103.json")
        receipt=json.loads(path.read_text())
        self.assertEqual(receipt["original_emulator_ticks"],list(TICKS))
        self.assertEqual(receipt["observed_RGB_red_component_5bit_addend"],13)
        rows=receipt["original_2D_source_correspondence_per_frame"]
        self.assertEqual([(x["original_emulator_tick"],x["original_OAM_slot"]) for x in rows],
                         [(tick,slot) for tick in TICKS for slot in (96,97)])
        for slot,expected_direct,expected_tint in (
                (96,[281,277,281,282,281],[35,39,39,41,36]),
                (97,[290,298,295,293,297],[21]*5)):
            selected=[r for r in rows if r["original_OAM_slot"]==slot]
            self.assertEqual([r["source_pixel_correspondence"]["direct_exact_RGB"]
                              for r in selected],expected_direct)
            self.assertEqual([r["source_pixel_correspondence"]["red_5bit_plus_13_RGB"]
                              for r in selected],expected_tint)
            self.assertEqual([r["source_pixel_correspondence"]["unaccounted_RGB"]
                              for r in selected],[0]*5)
            self.assertTrue(all(r["opposite_orientation_unaccounted"]>100 for r in selected))
            self.assertTrue(all(r["one_pixel_x_shift_unaccounted"]>100 for r in selected))
            self.assertTrue(all(r["red_bonus_12_instead_of_13_unaccounted"]>0 for r in selected))
        self.assertTrue(receipt["source_pixel_rgb_correspondence_with_two_observed_transform_states_verified"])
        for field in ("source_original_effective_per_scanline_OAM_flip_write_verified",
                      "source_original_pixel_layer_winner_or_colour_math_register_verified",
                      "source_1994_original_3D_geometry_rig_camera_verified",
                      "source_to_2026_GLB_pose_mapping_verified",
                      "owner_likeness_approved"):
            self.assertFalse(receipt[field])


if __name__=="__main__":
    unittest.main()
