"""Existing ART-4K Pages 3D viewer root-lean hypothesis controls, ROM-free."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]


class RootLeanViewerTests(unittest.TestCase):
    def test_real_existing_site_and_both_publishers_include_helper(self):
        html=(ROOT/"tools/art/model-review/index.html").read_text(encoding="utf-8")
        self.assertIn("import {rootLeanQuaternion,tireVisualLift} from './root_lean_hypothesis.mjs'",html)
        self.assertIn('id="rootLean"',html)
        self.assertIn('id="rootLeanStatus"',html)
        self.assertIn("applyRootLean()",html)
        self.assertIn("Original-ROM research",html)
        for path in ("tools/windows_visual_atlas.py","tools/art/model-review/stage_pages.py"):
            self.assertIn("root_lean_hypothesis.mjs",
                          (ROOT/path).read_text(encoding="utf-8"))

    @unittest.skipUnless(shutil.which("node"),"Node runtime unavailable")
    def test_quaternion_from_original_source_axis_and_reversible_zero(self):
        script=r"""
import assert from 'node:assert/strict';
import {ROOT_LEAN_PRESETS,rootLeanQuaternion,tireVisualLift} from './tools/art/model-review/root_lean_hypothesis.mjs';
assert.deepEqual(ROOT_LEAN_PRESETS,[0,-35,10,15,30]);
function near(a,b){assert.ok(Math.abs(a-b)<1e-12,'quaternion component mismatch')}
const base=rootLeanQuaternion(0,true);
near(base[0],-Math.SQRT1_2);near(base[1],0);near(base[2],0);near(base[3],Math.SQRT1_2);
for(const t of ROOT_LEAN_PRESETS){
 const a=rootLeanQuaternion(t,true);
 const b=rootLeanQuaternion(t,false);
 near(Math.hypot(...a),1);near(Math.hypot(...b),1);
 near(b[0],0);near(b[2],0);
 near(b[1],Math.sin(t*Math.PI/360));
 near(b[3],Math.cos(t*Math.PI/360));
}
assert.notDeepEqual(rootLeanQuaternion(-35,true),rootLeanQuaternion(15,true));
assert.deepEqual(rootLeanQuaternion(0,true),base);
// Actual source tire z-min under -35° rotation is approximately -0.1806955;
// the display-only correction must restore its original lower height.
near(tireVisualLift(0,-0.18069551607616607),0.18069551607616607);
near(tireVisualLift(0,-0.015039530784946737),0.015039530784946737);
near(tireVisualLift(0,0),0);
for(const pair of [[NaN,0],[0,Infinity],[Infinity,0]]){
 assert.throws(()=>tireVisualLift(...pair),/invalid/);
}
for(const n of [Infinity,NaN,1,5,-50,45,"15",null]){
 assert.throws(()=>rootLeanQuaternion(n,true),/unsupported/);
}
assert.throws(()=>rootLeanQuaternion(15,"true"),/unsupported/);
console.log("one existing model only, exact source quaternion, reversible zero");
"""
        run=subprocess.run(["node","--input-type=module","-e",script],
                           cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(run.returncode,0,run.stdout+"\n"+run.stderr)


if __name__=="__main__":
    unittest.main()
