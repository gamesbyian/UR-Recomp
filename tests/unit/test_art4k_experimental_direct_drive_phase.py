"""ROM-free direct-drive kinematics and real GLB safety regression controls."""
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.art import experimental_direct_drive_phase as drive


class DirectDrivePureTests(unittest.TestCase):
    def test_exact_five_source_phase_deltas(self):
        self.assertEqual({p: drive.delta_for_pose(p) for p in drive.SOURCE_PHASE},
                         {"upright":0,"pedal":70,"wheelie":26,"stunt":102,"bank":132})

    def test_openscad_crank_cos_sin_matches_rim_rotation(self):
        # Pedals in the source: [0.31*cos(phase), y, 0.31*sin(phase)].
        x,z=.31*math.cos(math.radians(18)),.31*math.sin(math.radians(18))
        for delta in (0,26,70,102,132,-70,180):
            r=drive.rotation(delta)
            self.assertAlmostEqual(r[0][0]*x+r[0][2]*z,
                                   .31*math.cos(math.radians(18+delta)),places=12)
            self.assertAlmostEqual(r[2][0]*x+r[2][2]*z,
                                   .31*math.sin(math.radians(18+delta)),places=12)

    def test_invalid_source_and_numeric_controls_rejected(self):
        for bad in (True,None,"","ride",123):
            with self.subTest(pose=bad),self.assertRaises(ValueError):
                drive.delta_for_pose(bad)
        for bad in (True,None,"18",float("nan"),float("inf"),-721,721):
            with self.subTest(delta=bad),self.assertRaises(ValueError):
                drive.rotation(bad)


try:
    import numpy as np
    import trimesh
except ImportError:
    np=trimesh=None


@unittest.skipUnless(np is not None and trimesh is not None, "offline numpy/trimesh only")
class SourceSceneTests(unittest.TestCase):
    def scene(self,bank=0):
        s=trimesh.Scene()
        a=math.radians(bank)
        m=np.eye(4)
        m[:3,:3]=[[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]]
        m[:3,3]=[-.2,0,1.3]
        for part in drive.PARTS:
            t=m.copy()
            if part=="saddle":
                t[:3,3]+=m[:3,:3]@np.array([.04,0,2.27])
            s.graph.update(frame_to=part,frame_from=s.graph.base_frame,matrix=t)
            for i in range(drive.CHILD_COUNTS[part]):
                name=f"{part}__material_{i}"
                s.add_geometry(trimesh.creation.box(extents=(.01,.01,.01)),
                               node_name=name,geom_name=name,parent_node_name=part)
        return s

    def test_real_banked_axle_preserves_crank_saddle_and_all_meshes(self):
        s=self.scene(bank=23)
        old={p:s.graph.get(p)[0].copy() for p in drive.PARTS}
        vertices={n:(m.vertices.copy(),m.faces.copy()) for n,m in s.geometry.items()}
        r=drive.synchronize(s,70)
        self.assertEqual(r["source_owned_relative_wheel_phase_degrees"],70.)
        expected=old["tire"]@np.asarray(drive.rotation(70))
        for p in drive.MOVING:
            np.testing.assert_allclose(s.graph.get(p)[0],expected,atol=1e-9,rtol=0)
        for p in drive.STATIONARY:
            np.testing.assert_array_equal(s.graph.get(p)[0],old[p])
        for n,m in s.geometry.items():
            np.testing.assert_array_equal(m.vertices,vertices[n][0])
            np.testing.assert_array_equal(m.faces,vertices[n][1])

    def test_zero_phase_identical_and_missing_mesh_rejected(self):
        s=self.scene()
        before={p:s.graph.get(p)[0].copy() for p in drive.PARTS}
        drive.synchronize(s,0)
        for p in drive.PARTS:
            np.testing.assert_array_equal(s.graph.get(p)[0],before[p])
        s.delete_geometry("tire__material_0")
        with self.assertRaisesRegex(ValueError,"sixteen"):
            drive.synchronize(s,70)

    def test_off_axis_pedals_or_rim_rejected(self):
        for p in ("pedals","rim_and_hub"):
            s=self.scene()
            t=s.graph.get(p)[0].copy()
            t[0,3]+=.25
            s.graph.update(frame_to=p,frame_from=s.graph.base_frame,matrix=t)
            with self.subTest(p=p),self.assertRaisesRegex(ValueError,"common rigid axle"):
                drive.synchronize(s,70)

    def test_real_glb_roundtrip_and_receipt_no_overwrite(self):
        scene=self.scene()
        b=scene.export(file_type="glb")
        with patch.dict(drive.SOURCE_GLBS,{"pedal":hashlib.sha256(b).hexdigest()}):
            derived,r=drive.build(b,"pedal")
            self.assertEqual(r["source_pedal_phase_degrees"],88.)
            self.assertEqual(r["derived_glb_sha256"],hashlib.sha256(derived).hexdigest())
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp)
                source=root/"source.glb"
                source.write_bytes(b)
                target,receipt=root/"derived.glb",root/"derived.json"
                drive.process(source,"pedal",target,receipt)
                self.assertEqual(json.loads(receipt.read_text()),r)
                with self.assertRaises(FileExistsError):
                    drive.process(source,"pedal",target,receipt)
        with self.assertRaisesRegex(ValueError,"SHA-pinned"):
            drive.build(b,"stunt")

    def test_receipt_collision_must_not_delete_foreign_writer(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            src=root/"source.glb"
            src.write_bytes(b"fixture")
            target,receipt=root/"derived.glb",root/"derived.json"
            link=drive.os.link
            def race(a,b):
                if Path(b)==receipt:
                    target.unlink()
                    target.write_bytes(b"foreign-writer")
                    raise FileExistsError("receipt collision")
                return link(a,b)
            with patch.object(drive,"build",return_value=(b"glTFdummy",{"schema":"test"})), \
                 patch.object(drive.os,"link",side_effect=race):
                with self.assertRaises(FileExistsError):
                    drive.process(src,"pedal",target,receipt)
            self.assertEqual(target.read_bytes(),b"foreign-writer")
            self.assertFalse(receipt.exists())


if __name__=="__main__":
    unittest.main()
