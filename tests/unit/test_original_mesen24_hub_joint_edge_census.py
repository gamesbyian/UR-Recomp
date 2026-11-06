"""Permanent original 1994 Mesen24 true edge deltas, no original raster redistribution."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"analysis/data/racer-art4k-mesen24-hub-kinematics-23-edge-deltas-20261105.json"
OLD=ROOT/"analysis/data/racer-art4k-mesen24-hub-attachment-qualified-20261105.json"

class SourceMesen24OriginalHubKinematicsEdges(unittest.TestCase):
    def test_all_real_23_edges_two_players_two_wheel_laws_conserved(self):
        data=json.loads(SRC.read_text())
        previous=json.loads(OLD.read_text())
        self.assertEqual(data["schema"],"UR-ART4K-AUTHENTIC-MESEN24-HUB-KINEMATICS-23-EDGE-DELTA-CENSUS/1")
        self.assertEqual(data["source_full_original_real_GLB_report_sha256"],previous["source_full_report_sha256"])
        self.assertEqual(data["source_original_USA_ROM_sha256"],previous["source_original_USA_ROM_sha256"])
        self.assertEqual(data["source_original_Mesen24_archive_sha256"],previous["source_original_Mesen24_no_skip_archive_sha256"])
        self.assertEqual(data["source_frozen_provisional_camera_sha256"],previous["source_unchanged_provisional_7_6_camera_sha256"])
        self.assertEqual(data["source_original_2026_SCAD_sha256"],previous["source_2026_authored_SCAD_sha256"])
        self.assertEqual(data["source_original_racers"],["blue","red"])
        self.assertEqual(data["source_original_frame_ticks_inclusive"],[1601,1624])
        self.assertEqual(data["source_original_real_consecutive_edges_per_racer"],23)
        self.assertEqual(set(data["source_only_two_predeclared_same_mechanics_wheel_laws"]),{"rom_phase_15deg","fixed_tick_24deg"})
        for role in ("blue","red"):
            for mode in ("rom_phase_15deg","fixed_tick_24deg"):
                edges=data["per_role_and_drive_23_actual_source_edge_changes"][role][mode]
                source=data["per_role_and_drive_23_actual_source_edge_tp_fp_fn_totals"][role][mode]
                self.assertEqual(len(edges),23)
                self.assertTrue(all(len(row)==4 and type(row[0]) in (int,float)
                                    and all(type(v)==int for v in row[1:])
                                    and -1<=row[0]<=1 for row in edges))
                locked,rotating=source["axle_locked"],source["wheel_rotating"]
                self.assertEqual(len(locked),3)
                self.assertEqual(len(rotating),3)
                self.assertEqual(locked[0]+locked[2],rotating[0]+rotating[2])
                self.assertEqual([sum(row[i] for row in edges) for i in (1,2,3)],
                                 [locked[i]-rotating[i] for i in range(3)])
                prior=previous["source_2026_model_physical_hub_attachment_score"][role][mode]
                for name,values in (("axle_locked",locked),("rotating",rotating)):
                    tp,fp,fn=values
                    self.assertEqual(round(tp/(tp+fp+fn),8),
                                     prior["per_2026_physical_hub_joint"][name]["source_actual_23_consecutive_edge_change_pooled_iou"])
        self.assertEqual(data["per_role_and_drive_23_actual_source_edge_changes"]["red"]["fixed_tick_24deg"][20],
                         [.09027778,4,-3,-4])

    def test_explicit_original_3d_and_owner_vetoes_remain(self):
        data=json.loads(SRC.read_text())
        for key in ("original_1994_3D_mesh_camera_or_physical_hub_joint_recovered",
                    "original_2026_artist_likeness_approved","shipping_art_approved"):
            self.assertIs(data[key],False)
        self.assertIs(data["retrospective_original_source_not_prospective_holdout"],True)

if __name__=="__main__":
    unittest.main()
