"""ROM-free negative controls for authored fork/tire rigid-pose inference."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

AVAILABLE=all(importlib.util.find_spec(name) is not None
              for name in ("numpy","trimesh"))
if AVAILABLE:
    import numpy as np
    from tools.art.verify_fork_pose_transport import (
        rigid_relative_pose, read_original_export, POSES,
    )


@unittest.skipUnless(AVAILABLE, "optional real-GLB model dependencies")
class PoseTransportMathTests(unittest.TestCase):
    def test_five_source_pose_contract_is_exact(self):
        self.assertEqual(POSES, ("upright","pedal","wheelie","stunt","bank"))

    def test_proper_shared_rotation_and_translation_preserve_relative_frame(self):
        upright=np.eye(4)
        rotate=np.array([[0.,-1.,0.,2.],[1.,0.,0.,-3.],
                         [0.,0.,1.,4.],[0.,0.,0.,1.]])
        expected,_=rigid_relative_pose(upright,upright)
        found,error=rigid_relative_pose(rotate,rotate,expected)
        self.assertLess(error,1e-14)
        np.testing.assert_allclose(found,expected,atol=1e-14)

    def test_authored_pedal_relative_motion_is_rejected(self):
        eye=np.eye(4)
        moved=np.eye(4)
        moved[0,3]=.02
        with self.assertRaisesRegex(ValueError,"unshared relative motion"):
            rigid_relative_pose(eye,moved,eye)

    def test_reflections_scaling_shear_and_nonfinite_fail_closed(self):
        eye=np.eye(4)
        wrong=[]
        reflect=eye.copy();reflect[1,1]=-1;wrong.append(reflect)
        scale=eye.copy();scale[0,0]=1.1;wrong.append(scale)
        shear=eye.copy();shear[0,1]=.03;wrong.append(shear)
        nan=eye.copy();nan[1,2]=float("nan");wrong.append(nan)
        for matrix in wrong:
            with self.subTest(matrix=repr(matrix)):
                with self.assertRaisesRegex(ValueError,"proper rigid"):
                    rigid_relative_pose(eye,matrix)

    def test_missing_source_export_never_guesses_glb(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                read_original_export(Path(d),"upright")
            with self.assertRaisesRegex(ValueError,"five authored"):
                read_original_export(Path(d),"unknown")


if __name__=="__main__":
    unittest.main()
