"""ROM-free negative and positive guards for actual continuous GLB export receipt."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"tools/art/candidates/unicycle_shared_rig.scad"
SCRIPT=ROOT/"tools/art/verify_art4k_real_continuous_glb.py"
spec=importlib.util.spec_from_file_location("real_art4k_continuous_glb_check",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def write_json(file, obj):
    file.write_text(json.dumps(obj,sort_keys=True)+"\n")
    return file


def fixture(root, pose="stunt_cycle", time=.5, player_palette="source"):
    source = root / "source.scad"
    source.write_bytes(SOURCE.read_bytes())
    import sys
    sys.path.insert(0,str(ROOT))
    from tools.art.continuous_pose_recipe import continuous_pose_recipe
    pedal,lean,matrix,meta=continuous_pose_recipe(source.read_text(),pose,time)
    out=root/"export"
    dest=out/"attempts"/"test-once"
    dest.mkdir(parents=True)
    glb=dest/"unicycle_articulated_blockout.glb"
    glb.write_bytes(b"mock-via-stub")
    sha=lambda d: hashlib.sha256(d).hexdigest()
    palette_expression, rgba = mod.PLAYER_PALETTES[player_palette]
    components=[
        {"name":k,"material_count":v,"editable_node":True,
         "materials":[{"node":f"{k}__material_{i}","rgba":list(color)}
                      for i,color in enumerate(mod.materials_for_part(
                          source.read_text(),k,rig_color_override=palette_expression))]}
        for k,v in mod.PART_MATERIAL_COUNTS.items()
    ]
    palette = {"schema_version":1, "id":player_palette,
               "override_rgba":list(rgba) if rgba else None,
               "original_raster_color_registered":False,
               "owner_material_approved":False}
    receipt={
        "schema":"ur-art4k-articulated-blockout/1",
        "attempt_id":"test-once","source_sha256":sha(source.read_bytes()),
        "rig_pose":pose,"glb_sha256":sha(glb.read_bytes()),"glb_size":glb.stat().st_size,
        "player_palette":palette,
        "pose_source_registered_to_original_game":False,
        "original_character_likeness_approved":False,
        "shipping_art_approved":False,
        "animation_cadence_source_registered":False,
        "pose_controls":{"pedal_phase_degrees":pedal,"saddle_lean_degrees":lean},
        "continuous_pose":meta,
        "source_pose_transform":[list(row) for row in matrix],
        "components":components,
        "glb_roundtrip":{"validated_parts":5,"validated_material_meshes":16},
    }
    file=write_json(dest/"articulated_blockout_receipt.json",receipt)
    pointer={
        "schema":"ur-art4k-export-current/1",
        "attempt_id":"test-once","source_sha256":receipt["source_sha256"],
        "rig_pose":pose,"player_palette":palette,
        "glb_path":"attempts/test-once/unicycle_articulated_blockout.glb",
        "receipt_path":"attempts/test-once/articulated_blockout_receipt.json",
        "glb_sha256":receipt["glb_sha256"],
        "receipt_sha256":sha(file.read_bytes()),
    }
    write_json(out/"articulated_blockout_current.json",pointer)
    write_json(out/"articulated_blockout_last_attempt.json",{
        "schema":"ur-art4k-export-attempt/1",
        "attempt_id":"test-once","source_sha256":receipt["source_sha256"],
        "status":"succeeded","current_output_usable":True,
        "glb_sha256":receipt["glb_sha256"],
    })
    return source,out,receipt,pointer


class RealContinuousGLBReceiptTests(unittest.TestCase):
    def test_ride_and_stunt_real_source_metadata(self):
        for pose,time in (("ride",.25),("stunt_cycle",.5)):
            with tempfile.TemporaryDirectory() as tmp:
                source,out,receipt,_=fixture(Path(tmp),pose,time)
                with patch.object(mod,"validate_glb_roundtrip",
                                  return_value=receipt["glb_roundtrip"]) as actual:
                    result=mod.validate_one(source,out,pose,time)
                self.assertEqual(result["part_material_mesh_count"],16)
                self.assertEqual(result["part_parent_count"],5)
                self.assertTrue(result["authored_continuous_source_kinematics_recomputed"])
                self.assertFalse(result["1994_source_cadence_or_pose_paired"])
                actual.assert_called_once()

    def test_source_bound_palette_selection_and_forgery_rejected(self):
        # No real GLB is claimed here: the loader is stubbed. This checks
        # identity binding; actual material geometry remains a separate gate.
        for palette_id in mod.PLAYER_PALETTES:
            with tempfile.TemporaryDirectory() as tmp:
                source,out,receipt,pointer=fixture(Path(tmp),player_palette=palette_id)
                with patch.object(mod,"validate_glb_roundtrip",
                                  return_value=receipt["glb_roundtrip"]) as loader:
                    qualified=mod.validate_one(source,out,"stunt_cycle",.5,
                                               player_palette=palette_id)
                self.assertEqual(qualified["player_palette"]["id"],palette_id)
                loader.assert_called_once()
                with patch.object(mod,"validate_glb_roundtrip") as forbidden:
                    with self.assertRaisesRegex(ValueError,"palette"):
                        mod.validate_one(source,out,"stunt_cycle",.5,
                                         player_palette=("p1-provisional-v1"
                                            if palette_id != "p1-provisional-v1" else "source"))
                    forbidden.assert_not_called()

        for field in ("pointer_id", "receipt_id", "approval", "forged_material_rgba"):
            with tempfile.TemporaryDirectory() as tmp:
                source,out,receipt,pointer=fixture(Path(tmp))
                if field == "pointer_id":
                    pointer["player_palette"]["id"]="p1-provisional-v1"
                elif field == "receipt_id":
                    receipt["player_palette"]["id"]="p2-provisional-v1"
                elif field == "approval":
                    receipt["player_palette"]["owner_material_approved"]=True
                else:
                    receipt["components"][2]["materials"][0]["rgba"]=[255,0,0,255]
                file=out/pointer["receipt_path"]
                write_json(file,receipt)
                pointer["receipt_sha256"]=mod.sha256(file.read_bytes())
                write_json(out/"articulated_blockout_current.json",pointer)
                with self.subTest(field=field), patch.object(
                        mod,"validate_glb_roundtrip") as forbidden:
                    with self.assertRaisesRegex(ValueError,"palette"):
                        mod.validate_one(source,out,"stunt_cycle",.5)
                    forbidden.assert_not_called()

    def test_stale_attempt_never_reuses_prior_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,out,receipt,pointer=fixture(Path(tmp))
            last=out/"articulated_blockout_last_attempt.json"
            current=json.loads(last.read_text())
            current["status"]="failed"
            write_json(last,current)
            with self.assertRaisesRegex(ValueError,"stale"):
                mod.validate_one(source,out,"stunt_cycle",.5)
            current["status"]="succeeded"
            current["attempt_id"]="later-incomplete"
            write_json(last,current)
            with self.assertRaisesRegex(ValueError,"stale"):
                mod.validate_one(source,out,"stunt_cycle",.5)

    def test_forged_kinematic_metadata_and_approval_rejected(self):
        for key, value in (
            ("continuous_pose", {"rig_time":.9}),
            ("pose_controls", {"pedal_phase_degrees":999,
                               "saddle_lean_degrees":0}),
            ("source_pose_transform", [[1,0,0,0]]*4),
            ("owner_character_likeness_approved", True),
        ):
            with tempfile.TemporaryDirectory() as tmp:
                source,out,receipt,pointer=fixture(Path(tmp))
                receipt[key]=value
                file=out/pointer["receipt_path"]
                write_json(file,receipt)
                pointer["receipt_sha256"]=mod.sha256(file.read_bytes())
                write_json(out/"articulated_blockout_current.json",pointer)
                with self.subTest(field=key),self.assertRaises(ValueError):
                    mod.validate_one(source,out,"stunt_cycle",.5)

    def test_changed_glb_and_path_escape_rejected_before_loader(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,out,receipt,pointer=fixture(Path(tmp))
            (out/pointer["glb_path"]).write_bytes(b"evil")
            with self.assertRaisesRegex(ValueError,"bytes changed"):
                mod.validate_one(source,out,"stunt_cycle",.5)
        with tempfile.TemporaryDirectory() as tmp:
            source,out,receipt,pointer=fixture(Path(tmp))
            pointer["glb_path"]="../secret.glb"
            write_json(out/"articulated_blockout_current.json",pointer)
            with self.assertRaisesRegex(ValueError,"escapes"):
                mod.validate_one(source,out,"stunt_cycle",.5)

    def test_qualified_receipt_publication_is_atomic_and_no_replace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = root / "qualified.json"
            mod.publish_receipt_no_replace(receipt, {"status": "qualified"})
            original = receipt.read_bytes()
            self.assertEqual(json.loads(original), {"status": "qualified"})
            with self.assertRaises(FileExistsError):
                mod.publish_receipt_no_replace(receipt, {"status": "forged"})
            self.assertEqual(receipt.read_bytes(), original)
            self.assertEqual(sorted(p.name for p in root.iterdir()), ["qualified.json"])

    def test_dangling_symlink_cannot_redirect_qualified_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = root / "qualified.json"
            foreign = root / "foreign.json"
            try:
                receipt.symlink_to(foreign)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            self.assertFalse(receipt.exists())
            with self.assertRaises(FileExistsError):
                mod.publish_receipt_no_replace(receipt, {"status": "qualified"})
            self.assertFalse(foreign.exists())
            self.assertTrue(receipt.is_symlink())
            self.assertEqual(sorted(p.name for p in root.iterdir()), ["qualified.json"])

    def test_publication_failure_leaves_no_partial_or_temp_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = root / "qualified.json"
            with patch.object(mod.os, "link",
                              side_effect=OSError("injected hard-link failure")):
                with self.assertRaisesRegex(OSError, "injected hard-link failure"):
                    mod.publish_receipt_no_replace(receipt, {"status": "qualified"})
            self.assertEqual(list(root.iterdir()), [])

    def test_cli_uses_no_replace_publication_for_qualified_receipt(self):
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = root / "qualified.json"
            foreign = root / "foreign.json"
            receipt.symlink_to(foreign)
            argv = ["verify_art4k_real_continuous_glb.py", "--source",
                    str(root / "source.scad"), "--output-dir", str(root),
                    "--pose", "ride", "--time", "0.25",
                    "--receipt", str(receipt)]
            with patch.object(sys, "argv", argv), patch.object(
                    mod, "validate_one", return_value={"schema": mod.SCHEMA}):
                with self.assertRaises(FileExistsError):
                    mod.main()
            self.assertFalse(foreign.exists())
            self.assertTrue(receipt.is_symlink())

    def test_invalid_times_and_unsupported_pose_fail_early(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,out,*_=fixture(Path(tmp))
            for time in (-.1,1.1,float("nan"),float("inf")):
                with self.subTest(time=time),self.assertRaises(ValueError):
                    mod.validate_one(source,out,"ride",time)
            with self.assertRaises(ValueError):
                mod.validate_one(source,out,"upright",.5)


if __name__=="__main__":
    unittest.main()
