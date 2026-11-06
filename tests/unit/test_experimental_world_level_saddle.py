"""ROM-free rigid-transform qualification for 2026 saddle leveling null."""
import unittest
from tools.art.experimental_world_level_saddle import world_level_target

ID=((1.,0.,0.),(0.,1.,0.),(0.,0.,1.))
Q=((0.,0.,1.),(0.,1.,0.),(-1.,0.,0.))

def world(rotation,xyz):
    return tuple(tuple(rotation[i][j] if j<3 else xyz[i] for j in range(4))
                 for i in range(3))+((0.,0.,0.,1.),)

class WorldAttitudePreservingSaddleTests(unittest.TestCase):
    def test_preserves_actual_moving_mount_position_but_not_world_angle(self):
        source=world(Q,(0.42,-0.24,1.97))
        level=world_level_target(source,ID)
        self.assertEqual(level,world(ID,(0.42,-0.24,1.97)))
        self.assertEqual(world_level_target(source,Q),source)
        self.assertNotEqual(level,source)
        self.assertEqual(level[3],source[3])
        self.assertEqual(tuple(row[3] for row in level[:3]),
                         tuple(row[3] for row in source[:3]))

    def test_invalid_rigid_or_reflection_is_rejected(self):
        source=world(Q,(0.,0.,1.))
        for current,rot in (
            (source,((1.,0.,0.),(0.,-1.,0.),(0.,0.,1.))),
            (source,((1.,0.,0.),(0.,1.,0.),(0.,0.,-1.))),
            (world(((2.,0.,0.),(0.,1.,0.),(0.,0.,1.)),(0.,0.,1.)),ID),
            (source,((1.,0.,0.),(0.,float("nan"),0.),(0.,0.,1.))),
            (source,((1.,0.,0.),(0.,1.,0.))),
            (source,True)):
            with self.subTest(current=current,rotation=rot),self.assertRaises(ValueError):
                world_level_target(current,rot)
        with self.assertRaises(ValueError):
            world_level_target(world(Q,(float("inf"),0.,1.)),ID)
        with self.assertRaises(ValueError):
            world_level_target(((0.,),),ID)

if __name__=="__main__":
    unittest.main()
