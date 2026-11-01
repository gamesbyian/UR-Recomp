"""ROM-free regression guards for bounded, existing-source frame-mass study."""
from __future__ import annotations

import hashlib
import math
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from types import SimpleNamespace
import inspect

from tools.art.ablate_racer_frame_mass import (
    CANONICAL_SOURCE_SHA, checked_masses, source_prefix, validate_scores,
    validate_frame_tire_overlap, export_fork_tire_csg, study,
)


def row(mask, players, iou, chamfer):
    return {
        "source_binary_mask_sha256":mask,
        "player_set":players,
        "mask_iou":iou,
        "boundary_chamfer_mean_physical_px":chamfer,
    }


class OriginalFrameMassAblationTests(unittest.TestCase):
    def test_bounded_existing_parameter_grid_requires_original_control(self):
        self.assertEqual(checked_masses([1,1.2,1.4,2]),[1.0,1.2,1.4,2.0])
        for values in ([],[1.1],[0.99,1.0],[1.0,2.1],[1.0,1.0],
                       [1.0,float("nan")],[1.0,float("inf")],
                       [1.0]+[1.1]*17):
            with self.subTest(values=values),self.assertRaises(ValueError):
                checked_masses(values)

    def test_unmodified_source_sha_and_known_entrypoint_required(self):
        data=(b"module fork_and_frame(){} \n"
              b"rig_frame_mass=is_undef(rig_frame_mass)?1:rig_frame_mass;\n"
              b"rig(rig_pose);\n")
        digest=hashlib.sha256(data).hexdigest()
        self.assertTrue(source_prefix(data,digest).endswith(";\n"))
        with self.assertRaisesRegex(ValueError, "SHA"):
            source_prefix(data,"0"*64)
        with self.assertRaisesRegex(ValueError, "entrypoint"):
            source_prefix(data.removesuffix(b"rig(rig_pose);\n"),
                          hashlib.sha256(data.removesuffix(b"rig(rig_pose);\n")).hexdigest())

    def test_one_vote_per_unique_original_shape(self):
        rows=[row("a"*64,["p1"],0.2,1.5),
              row("b"*64,["p1"],0.8,0.5),
              row("c"*64,["p2"],0.7,1.0)]
        result=validate_scores(rows,3)
        self.assertAlmostEqual(result["equal_original_binary_mask_weight_mean_iou"],.56666667,places=8)
        self.assertEqual(result["equal_original_binary_mask_weight_mean_chamfer_physical_px"],1)
        self.assertEqual(result["mean_by_original_player_group"]["p1"]["unique_source_shape_count"],2)
        self.assertEqual(result["mean_by_original_player_group"]["p2"]["mean_mask_iou"],.7)

    def test_same_source_aliases_cannot_get_extra_weight(self):
        rows=[row("a"*64,["p1"],.2,1.5),
              row("a"*64,["p1"],.2,1.5)]
        with self.assertRaisesRegex(ValueError,"exactly one vote"):
            validate_scores(rows,2)

    def test_invalid_chamfer_source_player_and_negative_iou_rejected(self):
        base=[row("a"*64,["p1"],.3,1.0)]
        for change in (
            {"mask_iou":-0.01},
            {"mask_iou":float("nan")},
            {"boundary_chamfer_mean_physical_px":float("nan")},
            {"boundary_chamfer_mean_physical_px":-1},
            {"player_set":["unknown"]},
            {"player_set":[]},
        ):
            trial=[dict(base[0],**change)]
            with self.subTest(change=change),self.assertRaises(ValueError):
                validate_scores(trial,1)

    def test_same_mask_can_consistently_represent_both_players(self):
        result=validate_scores([row("a"*64,["p1","p2"],.55,.78)],1)
        self.assertEqual(result["mean_by_original_player_group"]["p1"]["mean_mask_iou"],.55)
        self.assertEqual(result["mean_by_original_player_group"]["p2"]["mean_mask_iou"],.55)


class FrameTireExactCSGTests(unittest.TestCase):
    def test_valid_closed_intersection_reports_signed_volume_and_not_art_approval(self):
        record=validate_frame_tire_overlap(.018820749851,1058,1,True,True,"a"*64)
        self.assertAlmostEqual(record["fork_tire_intersection_csg_volume_model_units_cubed"],
                               .018820749851)
        self.assertEqual(record["fork_tire_intersection_connected_components"],1)
        self.assertTrue(record["fork_tire_intersection_csg_watertight"])
        self.assertFalse(record["fork_tire_intersection_is_mechanical_art_approval"])

    def test_unclosed_negative_infinite_or_false_provenance_is_rejected(self):
        base=[.001211679518,530,2,True,True,"b"*64]
        for at,value in ((0,float("nan")),(0,float("inf")),(0,0),(0,-1),
                         (1,0),(2,0),(3,False),(4,False),(5,"bad")):
            with self.subTest(at=at,value=value):
                args=list(base);args[at]=value
                with self.assertRaisesRegex(ValueError, "invalid/non-watertight"):
                    validate_frame_tire_overlap(*args)

    def test_exact_source_CSG_uses_both_unmodified_SCAD_modules_and_existing_mass(self):
        with TemporaryDirectory() as base:
            folder=Path(base)
            fake=SimpleNamespace(
                volume=.005606226026, faces=[0]*756,
                is_watertight=True, is_winding_consistent=True,
                split=lambda only_watertight: [1,2],
            )
            def render(command,**kwargs):
                self.assertEqual(command[:2],["openscad","-D"])
                self.assertIn("rig_frame_mass=1.4",command)
                text=Path(command[-1]).read_text()
                self.assertIn("rig_frame_mass=",text)
                self.assertEqual(text.count("translate([0,0,1]) fork_and_frame();"),1)
                self.assertEqual(text.count("translate([0,0,1]) tire();"),1)
                Path(command[command.index("-o")+1]).write_bytes(b"synthetic STL fixture")
                return SimpleNamespace(returncode=0,stderr="")
            with patch("tools.art.ablate_racer_frame_mass.subprocess.run",
                       side_effect=render),patch(
                         "tools.art.ablate_racer_frame_mass.trimesh",
                         SimpleNamespace(load_mesh=lambda *args,**kwargs: fake)):
                output=export_fork_tire_csg(
                    "rig_frame_mass=is_undef(rig_frame_mass)?1:rig_frame_mass;\n",
                    1.4,folder,"openscad")
            self.assertEqual(output["fork_tire_intersection_connected_components"],2)
            self.assertEqual(output["fork_tire_intersection_triangle_count"],756)
            self.assertTrue(output["fork_tire_intersection_csg_watertight"])

    def test_extra_CSG_work_is_optional_and_not_implicit_default(self):
        signature=inspect.signature(study)
        self.assertIs(signature.parameters["measure_frame_tire_csg"].default,False)


if __name__ == "__main__":
    unittest.main()
