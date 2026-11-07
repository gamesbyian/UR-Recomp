"""Real-material-sidedness geometry guards, executed only in rig venv."""
import unittest

try:
    import numpy as np
    import scipy
    import trimesh
except ModuleNotFoundError:
    np=scipy=trimesh=None

if np is not None and scipy is not None and trimesh is not None:
    from tools.art.verify_mirrored_outboard_tread_review import bilateral_tread_report

@unittest.skipUnless(np is not None and scipy is not None and trimesh is not None,
                     "real material geometry requires isolated art rig dependencies")
class MirroredTreadRealGeometryTests(unittest.TestCase):
    def test_central_inversion_on_actual_two_piece_triangle_mesh(self):
        points=[[.2,.436,.1],[.3,.436,.1],[.2,.442,.2]]
        points += [[-x,-y,-z] for x,y,z in points]
        mesh=trimesh.Trimesh(vertices=points,
            faces=[[0,1,2],[3,5,4]],process=False)
        # At least 8 per side is required to rule out degenerate test meshes.
        mesh=trimesh.util.concatenate([mesh,mesh.copy().apply_translation([0,0,0])])
        scene=trimesh.Scene()
        scene.add_geometry(mesh,geom_name="pedals__material_2")
        self.assertRaisesRegex(ValueError,"two opposite",bilateral_tread_report,scene)
        
    def test_mirror_observation_and_nonmirror_control(self):
        points=[]
        for sign in (1,-1):
            for x,y,z in ((.2,.436,.1),(.3,.436,.1),(.2,.442,.2),
                          (.3,.442,.2),(.2,.436,.2),(.3,.436,.2),
                          (.2,.442,.1),(.3,.442,.1)):
                points.append([sign*x,sign*y,sign*z])
        mesh=trimesh.Trimesh(vertices=points,
            faces=[[0,1,2],[4,5,6],[8,10,9],[12,14,13]],process=False)
        # Test geometry vertex counts are preserved by trimesh process=False.
        scene=trimesh.Scene()
        scene.add_geometry(mesh,geom_name="pedals__material_2")
        self.assertLess(bilateral_tread_report(scene)[
            "maximum_opposed_inverse_vertex_error"],1e-9)
        bad=mesh.copy();bad.vertices[8:,1]-=.248
        scene_bad=trimesh.Scene();scene_bad.add_geometry(bad,geom_name="pedals__material_2")
        self.assertGreater(bilateral_tread_report(scene_bad)[
            "maximum_opposed_inverse_vertex_error"],.20)

if __name__ == "__main__":
    unittest.main()
