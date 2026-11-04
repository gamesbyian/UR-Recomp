"""Test one original 2026 five-part GLB under fixed whole-rig pivot hypotheses."""
import hashlib
import json
import math
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.art import experimental_fixed_root_orbit as orbit

try:
    import numpy as np
    import trimesh
except ImportError:
    np=trimesh=None


class PureRootOrbitTests(unittest.TestCase):
    def test_bounded_root_index_and_two_authored_world_pivot_modes(self):
        self.assertEqual(orbit.MODES,("wheel_axle","historical_midbody"))
        self.assertEqual(orbit.MIDBODY_OFFSET_ABOVE_AXLE_WORLD_Z,0.8)
        identity=orbit.root_matrix(0,(0.,0.,1.8))
        for i in range(4):
            for j in range(4):
                self.assertAlmostEqual(identity[i][j],1. if i==j else 0.,places=12)
        quarter=orbit.root_matrix(16,(0.,0.,1.8))
        xyz=(0.,0.,1.,1.)
        projected=[sum(quarter[i][j]*xyz[j] for j in range(4)) for i in range(3)]
        self.assertAlmostEqual(projected[0],-0.8,places=12)
        self.assertAlmostEqual(projected[2],1.8,places=12)
        axle=orbit.root_matrix(16,(0.,0.,1.))
        self.assertAlmostEqual(sum(axle[0][j]*xyz[j] for j in range(4)),0.,places=12)
        self.assertAlmostEqual(sum(axle[2][j]*xyz[j] for j in range(4)),1.,places=12)
        for bad in (-1,64,1.5,True,"10",float("nan")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                orbit.root_matrix(bad,(0.,0.,1.8))
        with self.assertRaises(ValueError):
            orbit.root_matrix(2,(0.,0.,float("inf")))


@unittest.skipUnless(np is not None and trimesh is not None, "optional numpy/trimesh")
class SourceGLBRootOrbitTests(unittest.TestCase):
    def scene(self,intermediate=False):
        s=trimesh.Scene()
        parent="world"
        initial_parent=np.eye(4)
        if intermediate:
            a=math.radians(19)
            initial_parent[:3,:3]=[[math.cos(a),-math.sin(a),0.],
                                   [math.sin(a),math.cos(a),0.],[0.,0.,1.]]
            initial_parent[:3,3]=[4.,-2.,3.]
            s.graph.update(frame_to="world_1",frame_from="world",matrix=initial_parent)
            parent="world_1"
        for part in orbit.PARTS:
            initial=np.eye(4)
            initial[:3,3]=[0.,0.,1.]
            if part=="fork_and_frame":
                initial[2,3]+=0.3
            if part=="saddle":
                initial[2,3]+=2.2
            s.graph.update(frame_to=part,frame_from=parent,
                           matrix=np.linalg.inv(initial_parent)@initial)
            for i in range(orbit.CHILD_COUNTS[part] if hasattr(orbit,"CHILD_COUNTS") else
                           {"tire":2,"rim_and_hub":5,"fork_and_frame":4,"pedals":3,"saddle":2}[part]):
                node=f"{part}__material_{i}"
                s.add_geometry(trimesh.creation.box(extents=(.1,.2,.3)),
                               node_name=node,geom_name=node,parent_node_name=part)
        return s

    def test_absolute_root_and_axle_controls_share_unmodified_original_parts(self):
        for intermediate in (False,True):
            scene=self.scene(intermediate=intermediate)
            original={p:np.array(scene.graph.get(p)[0],copy=True) for p in orbit.PARTS}
            verts={key:(np.array(mesh.vertices,copy=True),np.array(mesh.faces,copy=True))
                   for key,mesh in scene.geometry.items()}
            result=orbit.apply_root_scene(scene,16,"historical_midbody",25,10)
            self.assertEqual(result["schema"],orbit.SCHEMA)
            self.assertFalse(result["original_1994_3D_angle_camera_or_joint_pivot_recovered"])
            self.assertEqual(len(scene.graph.nodes_geometry),16)
            axle=scene.graph.get("tire")[0][:3,3]
            np.testing.assert_allclose(axle,[-0.8,0,1.8],atol=1e-8,rtol=0)
            self.assertEqual(scene.graph.transforms.parents.get("tire"),
                             "world_1" if intermediate else "world")
            for k,v in scene.geometry.items():
                np.testing.assert_array_equal(v.vertices,verts[k][0])
                np.testing.assert_array_equal(v.faces,verts[k][1])
            orbit.apply_root_scene(scene,32,"wheel_axle",-25,-10)
            axle2=scene.graph.get("tire")[0][:3,3]
            np.testing.assert_allclose(axle2,[0,0,1],atol=1e-8,rtol=0)
            orbit.apply_root_scene(scene,0,"wheel_axle",0,0)
            for p in orbit.PARTS:
                np.testing.assert_allclose(scene.graph.get(p)[0],original[p],atol=1e-8,rtol=0)
            orbit.apply_root_scene(scene,16,"historical_midbody",15,0)
            t=scene.graph.get("tire")[0].copy()
            t[:3,3]+=[.3,0,0]
            scene.graph.update(frame_to="tire",
                               frame_from=scene.graph.transforms.parents["tire"],
                               matrix=np.linalg.inv(scene.graph.get("world_1")[0])@t if intermediate else t)
            with self.assertRaisesRegex(ValueError,"externally changed"):
                orbit.apply_root_scene(scene,5,"wheel_axle",0,0)

    def test_export_roundtrip_for_source_style_scene(self):
        scene=self.scene(intermediate=True)
        raw=scene.export(file_type="glb")
        key=hashlib.sha256(raw).hexdigest()
        with patch.object(orbit,"SOURCE_GLB_SHA256",key):
            output,record=orbit.build(raw,16,"historical_midbody",25,10)
            self.assertEqual(hashlib.sha256(output).hexdigest(),record["derived_GLB_sha256"])
            self.assertTrue(record["material_geometry_and_all_parent_matrices_survived_roundtrip"])
            self.assertFalse(record["shipping_art_approved"])
            with tempfile.TemporaryDirectory() as temp:
                base=Path(temp)
                src,glb,receipt=base/"source.glb",base/"derived.glb",base/"receipt.json"
                src.write_bytes(raw)
                orbit.process(src,16,"historical_midbody",25,10,glb,receipt)
                self.assertEqual(json.loads(receipt.read_text()),record)
                with self.assertRaises(ValueError):
                    orbit.process(src,16,"wheel_axle",25,10,glb,receipt)
        with self.assertRaisesRegex(ValueError,"exact SHA"):
            orbit.build(raw,16,"historical_midbody",0,0)

    def test_current_export_requires_validated_model_receipt_not_arbitrary_hash(self):
        # The exact source OpenSCAD can produce distinct GLB bytes per export.
        # A claimed hash alone is inadequate; require source-owned, checked
        # exporter receipt and the same exact on-disk GLB bytes.
        scene=self.scene(intermediate=True)
        raw=scene.export(file_type="glb")
        digest=hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            authenticated=root/"upright.glb"
            authenticated.write_bytes(raw)
            good_ptr={
                "source_sha256":orbit.HISTORICAL_SCAD_SHA,
                "glb_sha256":digest,
            }
            def valid(_, pose):
                self.assertEqual(pose,"upright")
                return good_ptr,{"glb":authenticated}
            with patch("runpy.run_path",return_value={"validate":valid}):
                output,receipt=orbit.build(raw,16,"wheel_axle",0,0,
                                           verified_export_root=root)
                self.assertEqual(receipt["source_2026_upright_GLb_sha256"],digest)
                self.assertEqual(receipt["source_2026_GLb_provenance_class"],
                                 "current_successful_source_scad_export_receipt")
                self.assertEqual(receipt["derived_GLB_sha256"],
                                 hashlib.sha256(output).hexdigest())
            bad_ptr=dict(good_ptr,source_sha256="0"*64)
            with patch("runpy.run_path",return_value={
                    "validate":lambda *_:(bad_ptr,{"glb":authenticated})}):
                with self.assertRaisesRegex(ValueError,"verified export"):
                    orbit.build(raw,16,"wheel_axle",0,0,
                                verified_export_root=root)
            with patch("runpy.run_path",return_value={
                    "validate":lambda *_:(good_ptr,{"glb":authenticated})}):
                with self.assertRaisesRegex(ValueError,"verified export"):
                    orbit.build(raw+b"X",16,"wheel_axle",0,0,
                                verified_export_root=root)
            with self.assertRaisesRegex(ValueError,"SHA-pinned"):
                orbit.build(raw,16,"wheel_axle",0,0)

    def test_bad_mode_does_not_mutate_source_parent_geometry(self):
        scene=self.scene()
        old={p:scene.graph.get(p)[0].copy() for p in orbit.PARTS}
        for mode in ("per_frame_fit",None,5):
            with self.assertRaises(ValueError):
                orbit.apply_root_scene(scene,15,mode,0,0)
            for p in orbit.PARTS:
                np.testing.assert_array_equal(scene.graph.get(p)[0],old[p])


if __name__=="__main__":
    unittest.main()
