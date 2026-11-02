"""ROM-free reversible experimental axle hinge in the existing Pages viewer."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


class FrameHingeViewerTests(unittest.TestCase):
    def test_existing_single_site_and_both_stagers_include_helper(self):
        html=(ROOT/"tools/art/model-review/index.html").read_text(encoding="utf-8")
        self.assertIn("from './frame_hinge_hypothesis.mjs'",html)
        self.assertIn('id="frameHinge"',html)
        self.assertIn('id="frameHingeStatus"',html)
        self.assertIn("captureFrameHinge()",html)
        self.assertIn("applyFrameHinge()",html)
        self.assertIn("frameHinge=0;frameHingeState=captureFrameHinge()",html)
        self.assertIn("const k=axle.clone().multiply(r).multiply(axle.clone().invert())",html)
        self.assertIn("k.clone().multiply(original.matrix)",html)
        self.assertIn("node.position.copy(original.position)",html)
        self.assertIn("node.quaternion.copy(original.quaternion)",html)
        self.assertIn("node.scale.copy(original.scale)",html)
        self.assertIn("meshes.length!==16",html)
        browser=(ROOT/"tools/art/model-review/browser-smoke.mjs").read_text(encoding="utf-8")
        self.assertIn("synthetic tire-only GLB falsely enabled axle hinge",browser)
        self.assertIn("real five-parent frame hinge unavailable",browser)
        self.assertIn("frame hinge failed to reset original pose",browser)
        self.assertIn("frame hinge altered stationary",browser)
        self.assertIn("frame hinge 0 degree reset mutated original source transforms",browser)
        self.assertIn("hingeStatus.dataset[key]",html)
        for path in ("tools/windows_visual_atlas.py","tools/art/model-review/stage_pages.py"):
            self.assertIn("frame_hinge_hypothesis.mjs",
                          (ROOT/path).read_text(encoding="utf-8"))

    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_exact_source_world_y_and_reversible_zero(self):
        code=r"""
import assert from 'node:assert/strict';
import {FRAME_HINGE_PRESETS,frameHingeSourceRotation} from './tools/art/model-review/frame_hinge_hypothesis.mjs';
assert.deepEqual(FRAME_HINGE_PRESETS,[0,-40,-20,20,40]);
function near(a,b){assert.ok(Math.abs(a-b)<1e-12)}
for(const p of FRAME_HINGE_PRESETS){
 const m=frameHingeSourceRotation(p),a=p*Math.PI/180;
 assert.equal(m.length,16);
 near(m[0],Math.cos(a));near(m[2],-Math.sin(a));near(m[8],Math.sin(a));
 near(m[10],Math.cos(a));
 assert.deepEqual([m[5],m[15]],[1,1]);
}
const identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
assert.deepEqual(frameHingeSourceRotation(0),identity);
for(const x of [NaN,Infinity,-50,45,1,'20',null,undefined]){
 assert.throws(()=>frameHingeSourceRotation(x),/unsupported/);
}
console.log('reversible GLB parent-only rotation presets, no new original game pose claims');
"""
        run=subprocess.run(["node","--input-type=module","-e",code],
                           cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(run.returncode,0,run.stdout+"\n"+run.stderr)


if __name__=="__main__":
    unittest.main()
