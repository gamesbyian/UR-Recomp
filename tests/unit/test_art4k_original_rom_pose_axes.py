"""ROM-free re-audit of original 24x64 source-index axis counterfactual."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import unittest

from tools.art.analyze_original_rom_pose_axes import (
    SCHEMA,ROM_SHA,SOURCE_POSE_REPORT_SHA,EVENTS,LIVE_ANGLES,changed,score,bbox,audit
)

ROOT=Path(__file__).resolve().parents[2]
FILE=ROOT/"analysis/data/racer-original-ROM-24phase-64angle-source-axis-20261103.json"
SHA="23aa563c094471a3d7f1b5dcb12489cc1b5ca45b1240aee06fde3934a932bbd0"


class RomAxisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=FILE.read_bytes()
        cls.report=json.loads(cls.raw)

    def test_exact_original_rom_source_hash_and_no_3d_overclaim(self):
        self.assertNotIn(b"\r",self.raw)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),SHA)
        r=self.report
        self.assertEqual(r["schema"],SCHEMA)
        self.assertEqual(r["original_authenticated_USA_ROM_sha256"],ROM_SHA)
        self.assertEqual(r["exact_authenticated_original_48_frame_pose_report_sha256"],
                         SOURCE_POSE_REPORT_SHA)
        self.assertEqual(r["original_ROM_24phase_64angle_exact_source_frame_count"],1536)
        self.assertTrue(r["original_observed_source_event_counterfactuals_are_retrospective"])
        self.assertTrue(r["original_source_2d_phase_axis_independent_of_3d_rig_physical_spin"])
        self.assertFalse(r["original_1994_3d_angle_camera_mesh_material_or_bone_mapping_recovered"])
        self.assertFalse(r["original_2026_rig_likeness_owner_approved"])
        self.assertEqual(r["source_phase_variation_positions_any_angle_count"],797)
        self.assertEqual(r["source_phase_variation_all_angles_bbox_xyxy"],[17,4,46,35])
        self.assertEqual(len(r["source_phase_variation_bbox_by_ROM_angle_index"]),64)

    def test_original_upper_colour_changes_exclusively_angle_axis_for_both_paths(self):
        data=self.report["two_original_upper_source_events"]
        self.assertEqual(set(data),set(EVENTS))
        for who,row in data.items():
            frm,to,lo,hi=EVENTS[who]
            self.assertEqual(row["actual_original_ticks"],[frm,to])
            self.assertEqual(row["original_source_upper_observed_y_inclusive"],[lo,hi])
            self.assertTrue(row["source_upper_change_independent_of_phase_order"])
            upper=row["actual_original_index_delta"]["observed_source_upper_third"]
            expected={"blue":(72,27,45),"red":(55,20,35)}[who]
            self.assertEqual((upper["index4bpp_changed_pixels"],
                              upper["alpha_xor_pixels"],
                              upper["shared_opaque_index_changed_pixels"]),expected)
            for path,phase,angle in [
                ("phase_first_then_angle","hold_angle_change_phase","hold_final_phase_change_angle"),
                ("angle_first_then_phase","hold_final_angle_change_phase","hold_phase_change_angle")
            ]:
                stages=row[path]
                self.assertEqual(stages[phase]["observed_source_upper_third"],
                                 {"index4bpp_changed_pixels":0,
                                  "alpha_xor_pixels":0,
                                  "shared_opaque_index_changed_pixels":0})
                self.assertEqual(stages[angle]["observed_source_upper_third"],upper)
            self.assertEqual(row["actual_original_index_delta"]["whole_64px"][
                "index4bpp_changed_pixels"],{"blue":280,"red":311}[who])

    def test_actual_angle_variants_are_upper_phase_invariant_but_not_all_64(self):
        report=self.report
        actual=report["source_phase_variation_by_actually_observed_ROM_angle"]
        self.assertEqual(set(actual),{str(a) for a in LIVE_ANGLES})
        reference={57:(118,50,[33,22,44,33]),
                   58:(115,47,[32,23,43,34]),
                   60:(116,52,[30,24,41,35]),
                   61:(117,54,[29,24,40,35])}
        for angle,(index_count,alpha_count,box) in reference.items():
            row=actual[str(angle)]
            self.assertEqual(row["distinct_source_index_positions_across_24_phase_states"],
                             index_count)
            self.assertEqual(row["distinct_source_alpha_positions_across_24_phase_states"],
                             alpha_count)
            self.assertEqual(row["source_index_variant_region_bbox_xyxy"],box)
            self.assertEqual(row["index_pixels_in_y_0_15_change_as_phase_varies"],0)
        # At extreme original angles, the 2D rotating region reaches y=4.
        self.assertEqual(report["source_phase_variation_all_angles_bbox_xyxy"][1],4)

    def test_synthetic_changes_and_coordinates(self):
        a=bytearray(4096)
        b=bytearray(4096)
        # x=3 at y4: alpha appears. x=5 at y4: opaque index changes.
        a[4*64+5]=3
        b[4*64+3]=2
        b[4*64+5]=7
        row=changed(bytes(a),bytes(b),4,4)
        self.assertEqual(row,{"index4bpp_changed_pixels":2,
                              "alpha_xor_pixels":1,
                              "shared_opaque_index_changed_pixels":1})
        self.assertEqual(score(bytes(a),bytes(b),4,4)[
            "observed_source_upper_third"],row)
        self.assertEqual(bbox({4*64+3,5*64+6}),[3,4,6,5])
        self.assertIsNone(bbox(set()))
        with self.assertRaises(ValueError):
            changed(b"",bytes(b),4,4)

    def test_wrong_rom_or_prior_pose_identity_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"wrong authenticated"):
            audit(b"",b"")
        with self.assertRaisesRegex(ValueError,"wrong authenticated"):
            audit(bytes(2*1024*1024),b"bad")


if __name__=="__main__":
    unittest.main()
