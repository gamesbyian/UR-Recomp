"""Source-gated direct-drive mechanics in the existing single Pages 3D viewer."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


class SourceDriveViewerTests(unittest.TestCase):
    def test_single_site_and_both_original_publishers(self):
        html=(ROOT/"tools/art/model-review/index.html").read_text()
        for marker in ("from './direct_drive_hypothesis.mjs'",
                       'id="wheelDrive"','id="wheelDriveStatus"',
                       "captureWheelDrive(origin)", "applyWheelDrive()",
                       "node.position.copy(old.position)", "node.quaternion.copy(old.quaternion)",
                       "k.clone().multiply(old.matrix).decompose"):
            self.assertIn(marker,html)
        for file in ("tools/windows_visual_atlas.py","tools/art/model-review/stage_pages.py"):
            self.assertIn("direct_drive_hypothesis.mjs",(ROOT/file).read_text())
        smoke=(ROOT/"tools/art/model-review/browser-smoke.mjs").read_text()
        for marker in ("synthetic non-source GLB falsely enabled direct drive",
                       "direct drive failed to rotate","direct drive moved stationary",
                       "direct drive source matrices not restored",
                       "wheel sync altered independent fork hinge",
                       "combined drive reset did not restore wheel"):
            self.assertIn(marker,smoke)

    @unittest.skipUnless(shutil.which("node"),"node unavailable")
    def test_source_shalock_and_ry_sign_exact(self):
        program=r"""
import assert from 'node:assert/strict';
import {SOURCE_SHA,PEDAL_PHASE,sourcePhaseDelta,sourceDriveMatrix}
 from './tools/art/model-review/direct_drive_hypothesis.mjs';
const expected={upright:0,pedal:70,wheelie:26,stunt:102,bank:132};
function near(a,b){assert.ok(Math.abs(a-b)<1e-12)}
for(const [pose,d] of Object.entries(expected)){
 assert.equal(sourcePhaseDelta(pose,SOURCE_SHA),d);
 const r=sourceDriveMatrix(pose,SOURCE_SHA),a=d*Math.PI/180;
 near(r[0],Math.cos(a));near(r[2],Math.sin(a));
 near(r[8],-Math.sin(a));near(r[10],Math.cos(a));
 assert.equal(r.length,16);
}
assert.deepEqual(sourceDriveMatrix('upright',SOURCE_SHA),
 [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
for(const [pose,sha] of [['ride',SOURCE_SHA],['upright','bad'],
                          [undefined,SOURCE_SHA],[null,SOURCE_SHA]]){
 assert.throws(()=>sourceDriveMatrix(pose,sha),/unavailable/);
}
console.log('source-locked direct-drive math and exact reset PASS');
"""
        run=subprocess.run(["node","--input-type=module","-e",program],cwd=ROOT,
                           capture_output=True,text=True,timeout=20)
        self.assertEqual(run.returncode,0,run.stdout+"\n"+run.stderr)


if __name__=="__main__":
    unittest.main()
