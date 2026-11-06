"""Oriented 2026 GLB surface digest is stable under legitimate export ordering."""
import hashlib
import unittest
from tools.art.fingerprint_authored_glb_surface import (
    PART_COUNTS,SCHEMA,canonical_triangle_sha,inspect_glb,
)

try:
    import numpy as np
    import trimesh
except ImportError:
    np=trimesh=None


@unittest.skipUnless(np is not None and trimesh is not None,"offline 2026 GLB dependencies")
class OrientedSurfaceFingerprint(unittest.TestCase):
    def scene(self,vertex_order=False,flip_winding=False,
              shift_saddle=False, recolour=False,move_parent=False):
        scene=trimesh.Scene()
        for part,n in PART_COUNTS.items():
            mat=np.eye(4)
            mat[:3,3]=[0.,0.,2.31 if part=="saddle" else 1.0]
            if move_parent and part=="saddle":mat[0,3]+=.3
            scene.graph.update(frame_to=part,
                               frame_from=scene.graph.base_frame,matrix=mat)
            for i in range(n):
                name=f"{part}__material_{i}"
                mesh=trimesh.creation.box(extents=(.20+.01*i,.3,.40))
                v=np.asarray(mesh.vertices).copy()
                f=np.asarray(mesh.faces).copy()
                if vertex_order:
                    perm=np.roll(np.arange(len(v)),3)
                    inverse=np.argsort(perm)
                    v=v[perm]
                    f=inverse[f]
                    f=np.roll(f[::-1],1,axis=1) # cyclic; preserve winding
                if flip_winding and name=="saddle__material_1":
                    f[0,[0,1]]=f[0,[1,0]]
                if shift_saddle and name=="saddle__material_1":
                    v[0,0]+=.25
                candidate=trimesh.Trimesh(vertices=v,faces=f,process=False)
                colour=np.array([50+i,80+i,100+i,255],dtype=np.uint8)
                if recolour and name=="saddle__material_1":colour[0]+=1
                candidate.visual.vertex_colors=np.tile(colour,(len(v),1))
                candidate.metadata["file_path"]=(
                    "/tmp/random-source-authoring-A" if not vertex_order
                    else "/tmp/random-source-authoring-B")
                scene.add_geometry(candidate,geom_name=name,node_name=name,
                                   parent_node_name=part)
        return scene

    def fingerprint(self,scene):
        raw=scene.export(file_type="glb")
        return inspect_glb(raw,expected_sha256=hashlib.sha256(raw).hexdigest())

    def test_nondeterministic_metadata_and_order_keep_oriented_surface(self):
        a=self.fingerprint(self.scene())
        b=self.fingerprint(self.scene(vertex_order=True))
        self.assertEqual(a["schema"],SCHEMA)
        self.assertEqual(a["exact_material_children"],16)
        self.assertEqual(a["exact_parent_parts"],5)
        self.assertEqual(
            a["authored_2026_geometry_colour_parent_pose_fingerprint_sha256"],
            b["authored_2026_geometry_colour_parent_pose_fingerprint_sha256"])
        self.assertEqual(set(a["source_materials"]),set(b["source_materials"]))
        self.assertNotEqual(a["input_GLb_sha256"],b["input_GLb_sha256"])

    def test_reversed_winding_changed_surface_colour_or_saddle_pivot_are_detected(self):
        old=self.fingerprint(self.scene())
        digest=old["authored_2026_geometry_colour_parent_pose_fingerprint_sha256"]
        for options in (
                {"flip_winding":True},
                {"shift_saddle":True},
                {"recolour":True},
                {"move_parent":True}):
            with self.subTest(options=options):
                changed=self.fingerprint(self.scene(**options))
                self.assertNotEqual(
                    changed["authored_2026_geometry_colour_parent_pose_fingerprint_sha256"],
                    digest)

    def test_wrong_source_glb_sha_and_structure_fail(self):
        raw=self.scene().export(file_type="glb")
        with self.assertRaisesRegex(ValueError,"byte/SHA"):
            inspect_glb(raw,expected_sha256="0"*64)
        with self.assertRaisesRegex(ValueError,"byte/SHA"):
            inspect_glb(b"not glb")
        wrong=self.scene()
        node="saddle__material_1"
        wrong.graph.transforms.remove_node(node)
        with self.assertRaisesRegex(ValueError,"five-parent sixteen-material"):
            self.fingerprint(wrong)

    def test_canonical_triangle_permutations_preserve_face_orientation(self):
        vertices=np.array([[0,0,0],[1,0,0],[0,1,0],[2,0,0]],dtype=np.float32)
        f=np.array([[0,1,2],[1,3,2]],dtype=int)
        a=canonical_triangle_sha(vertices,f)
        self.assertEqual(a,canonical_triangle_sha(vertices,[[1,2,0],[3,2,1]]))
        self.assertEqual(a,canonical_triangle_sha(vertices,f[::-1]))
        self.assertNotEqual(a,canonical_triangle_sha(vertices,[[0,2,1],[1,3,2]]))
        with self.assertRaises(ValueError):
            canonical_triangle_sha(vertices,[[0,1,4]])


if __name__=="__main__":
    unittest.main()
