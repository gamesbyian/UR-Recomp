"""Bounded authored continuous-rig transform and fail-closed source controls."""
from __future__ import annotations

import importlib.util
import math
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2] / "tools/art/continuous_pose_recipe.py"
spec = importlib.util.spec_from_file_location("continuous_pose_recipe", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SOURCE = '''
function unit_time(t)=min(1,max(0,t));
function ease_time(t)=let(u=unit_time(t)) u*u*(3-2*u);
module continuous_rig(time,spin=false){
 u=unit_time(time);pitch=spin?360*ease_time(u):0;
 translate([0,0,1.80]) rotate([0,-pitch,0]) translate([0,0,-1.80])
 rotate([3*sin(720*u),0,7*sin(360*u)])
 shared_rig(pedal=18+720*u,seat_lean=3*sin(360*u));
}
module rig(p){
 else if(p=="ride")continuous_rig(rig_time,false);
 else if(p=="stunt_cycle")continuous_rig(rig_time,true);
}
'''


class ContinuousRigTests(unittest.TestCase):
    def test_ride_start_is_identity(self):
        pedal, lean, matrix, meta = module.continuous_pose_recipe(SOURCE, "ride", 0)
        self.assertEqual((pedal, lean), (18, 0))
        self.assertEqual(matrix, ((1., 0., 0., 0.), (0., 1., 0., 0.),
                                  (0., 0., 1., 0.), (0., 0., 0., 1.)))
        self.assertTrue(meta["source_formula_validated"])

    def test_ride_quarter_sample_has_authored_wobble_and_bank(self):
        pedal, lean, matrix, meta = module.continuous_pose_recipe(SOURCE, "ride", .25)
        self.assertEqual(pedal, 198)
        self.assertEqual(lean, 3)
        self.assertAlmostEqual(meta["continuous_bank_degrees"], 7)
        self.assertAlmostEqual(meta["continuous_wobble_degrees"], 0, places=10)
        self.assertAlmostEqual(matrix[0][0], math.cos(math.radians(7)))

    def test_spin_halfway_uses_eased_180_degree_pivot(self):
        pedal, lean, matrix, meta = module.continuous_pose_recipe(SOURCE, "stunt_cycle", .5)
        self.assertEqual(pedal, 18)
        self.assertEqual(meta["pedal_phase_unwrapped_degrees"], 378)
        self.assertEqual(meta["continuous_pitch_degrees"], 180)
        self.assertAlmostEqual(matrix[2][3], 3.6)

    def test_end_cycle_has_720_degree_crank_and_360_degree_spin(self):
        pedal, lean, matrix, meta = module.continuous_pose_recipe(SOURCE, "stunt_cycle", 1)
        self.assertEqual(pedal, 18)
        self.assertEqual(meta["pedal_phase_unwrapped_degrees"], 738)
        self.assertEqual(meta["continuous_pitch_degrees"], 360)
        self.assertAlmostEqual(matrix[2][3], 0, places=10)

    def test_changed_authored_bank_amplitude_changes_output(self):
        changed = SOURCE.replace("7*sin(360*u)", "11*sin(360*u)")
        _, _, _, meta = module.continuous_pose_recipe(changed, "ride", .25)
        self.assertAlmostEqual(meta["continuous_bank_degrees"], 11)

    def test_unsupported_source_mutation_refused(self):
        for changed in (SOURCE.replace("u*u*(3-2*u)", "u"),
                        SOURCE.replace("rotate([0,-pitch,0])", "rotate([0,pitch,0])"),
                        SOURCE.replace("1.80])", "1.90])", 1),
                        SOURCE + SOURCE):
            with self.subTest(changed=changed[-40:]), self.assertRaises(ValueError):
                module.continuous_pose_recipe(changed, "ride", .5)

    def test_duplicate_function_overrides_fail_closed(self):
        # OpenSCAD's later declaration overrides the canonical source even
        # when its formal parameter differs. No GLB may receive a mismatched
        # authored-pose transform or misleading source-bound receipt.
        for override in ("function unit_time(x)=0;",
                         "function ease_time(x)=0;",
                         "function helper(x)=x; function helper(y)=0;"):
            with self.subTest(override=override), self.assertRaisesRegex(
                    ValueError, "duplicate OpenSCAD function declaration"):
                module.continuous_pose_recipe(SOURCE + override, "stunt_cycle", .25)

    def test_comment_only_function_text_does_not_trigger_override(self):
        source = SOURCE + "\n// function unit_time(x)=0;\n/* function ease_time(x)=0; */\n"
        pedal, lean, _, meta = module.continuous_pose_recipe(source, "ride", .25)
        self.assertEqual((pedal, lean), (198, 3))
        self.assertTrue(meta["source_formula_validated"])

    def test_invalid_time_refused(self):
        for time in (-.1, 1.1, float("nan"), float("inf"), "0.5"):
            with self.subTest(time=time), self.assertRaises(ValueError):
                module.continuous_pose_recipe(SOURCE, "ride", time)


if __name__ == "__main__":
    unittest.main()
