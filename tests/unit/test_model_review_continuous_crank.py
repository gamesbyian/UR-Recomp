"""ROM-free 64-step model-review wheel/crank math and static UI wiring."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


class ContinuousCrankViewerTests(unittest.TestCase):
    def test_existing_viewer_includes_source_gated_continuous_scrub(self):
        html=(ROOT/"tools/art/model-review/index.html").read_text()
        for frag in ('id="crankScrub"','id="crankStep"','id="crankStatus"',
                     'min="0" max="64" step="1"',
                     'sourceCrankMatrix(crankStep)',
                     'sourceWheelPoseMatrix(selected,manifest.source_model_sha256,crankStep)',
                     'cranks.position.copy(source.position)',
                     'if(next===0&&previous!==0)wheelDrive=driveBeforeScrub',
                     'frameHingeState=captureFrameHinge();'):
            self.assertIn(frag,html)
        self.assertIn("min-height:44px;touch-action:pan-x",html)
        smoke=(ROOT/"tools/art/model-review/browser-smoke.mjs").read_text()
        for frag in ("continuous crank slider touch target",
                     "synthetic non-source GLB falsely enabled crank scrub",
                     "continuous crank failed to advance",
                     "continuous crank moved independent",
                     "720-degree crank did not return pedals exactly",
                     "drive-enabled preference lost after crank scrub",
                     "continuous crank changed original GLB identity"):
            self.assertIn(frag,smoke)
        self.assertIn("direct_drive_hypothesis.mjs",
                      (ROOT/"tools/art/model-review/stage_pages.py").read_text())
        self.assertIn("direct_drive_hypothesis.mjs",
                      (ROOT/"tools/windows_visual_atlas.py").read_text())

    @unittest.skipUnless(shutil.which("node"),"Node not installed")
    def test_exact_64_step_source_math_and_safeguards(self):
        script=r"""
import assert from 'node:assert/strict';
import {SOURCE_SHA,CRANK_STEPS,sourceCrankDegrees,sourceCrankMatrix,
        sourceWheelPoseMatrix,sourceDriveMatrix}
  from './tools/art/model-review/direct_drive_hypothesis.mjs';
const I=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
function near(a,b){assert.ok(Math.abs(a-b)<1e-12);}
assert.equal(CRANK_STEPS,64);
for(let i=0;i<=64;i++){
 const deg=sourceCrankDegrees(i),r=sourceCrankMatrix(i);
 assert.equal(deg,i*11.25);
 near(r[0],Math.cos(deg*Math.PI/180));
 near(r[2],Math.sin(deg*Math.PI/180));
 near(r[8],-Math.sin(deg*Math.PI/180));
}
for(const step of [0,32,64])assert.deepEqual(sourceCrankMatrix(step),I);
for(const step of [1,2,3])assert.notDeepEqual(sourceCrankMatrix(step),I);
assert.deepEqual(sourceWheelPoseMatrix('pedal',SOURCE_SHA,0),
                 sourceDriveMatrix('pedal',SOURCE_SHA));
assert.deepEqual(sourceWheelPoseMatrix('pedal',SOURCE_SHA,64),
                 sourceDriveMatrix('pedal',SOURCE_SHA));
for(const bad of [-1,65,1.5,NaN,Infinity,'1',true,null,undefined])
 assert.throws(()=>sourceCrankDegrees(bad),/unsupported/);
assert.throws(()=>sourceWheelPoseMatrix('bad',SOURCE_SHA,1),/unavailable/);
assert.throws(()=>sourceWheelPoseMatrix('pedal','bad',1),/unavailable/);
console.log('source-authored 64-step crank math PASS');
"""
        r=subprocess.run(["node","--input-type=module","-e",script],cwd=ROOT,
                         capture_output=True,text=True,timeout=20)
        self.assertEqual(r.returncode,0,r.stdout+"\n"+r.stderr)


if __name__=="__main__":
    unittest.main()
