"""ART-4K existing Pages 3D viewer reversible wheel A/B geometry tests.

The pure .mjs implementation has no CDN dependencies. Run its actual JS
against light mock Three.js BufferAttributes when Node is available.
"""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "tools/art/model-review/wheel_hypothesis.mjs"
HTML = ROOT / "tools/art/model-review/index.html"


class WheelHypothesisViewerTests(unittest.TestCase):
    def test_existing_viewer_both_publication_paths_copy_helper(self):
        page = HTML.read_text(encoding="utf-8")
        self.assertIn("import {applyWheelWidthHypothesis} from './wheel_hypothesis.mjs'", page)
        self.assertIn('id="wheelOriginal"', page)
        self.assertIn('id="wheelWide"', page)
        self.assertIn("chooseWheelWidth(1.1)", page)
        self.assertIn("19 new original 2D silhouettes", page)
        self.assertIn("Experimental", page)
        for source in ("tools/windows_visual_atlas.py",
                       "tools/art/model-review/stage_pages.py"):
            self.assertIn("wheel_hypothesis.mjs",
                          (ROOT / source).read_text(encoding="utf-8"))

    @unittest.skipUnless(shutil.which("node"), "Node unavailable; source static checks still run")
    def test_js_selective_byte_exact_restore_and_fail_closed(self):
        script = r"""
import assert from 'node:assert/strict';
import {applyWheelWidthHypothesis as apply} from './tools/art/model-review/wheel_hypothesis.mjs';
const slots = ['tire__material_0','tire__material_1',
  ...Array.from({length:5},(_,i)=>'rim_and_hub__material_'+i)];
function attr(array) {
  return {array:new Float32Array(array), itemSize:3, count:array.length/3,
    setXYZ(i,x,y,z){this.array.set([x,y,z],i*3)}};
}
function mesh(name) {
 const position=attr([1,2,3,-2,4,5]),normal=attr([0.6,0.8,0,0,0,1]);
 const geometry={getAttribute(k){return k==='position'?position:k==='normal'?normal:null},
   computeBoundingBox(){this.box=true},computeBoundingSphere(){this.sphere=true}};
 return {isMesh:true,name,geometry,position,normal};
}
const wheel=slots.map(mesh), saddle=mesh('saddle__material_0');
const root={traverse(fn){for(const node of [...wheel,saddle])fn(node)}};
const before=wheel.map(o=>({
 pos:new Uint8Array(o.position.array.buffer.slice(0)),
 norm:new Uint8Array(o.normal.array.buffer.slice(0))
}));
const saddleBefore=saddle.position.array.slice();
assert.equal(apply(root,1.1).modifiedMaterialMeshes,7);
assert.ok(wheel.every(o=>o.position.array[0]>1&&o.geometry.box&&o.geometry.sphere));
assert.deepEqual(saddle.position.array,saddleBefore);
assert.equal(apply(root,1).wheelAndRimWorldXFactor,1);
wheel.forEach((o,i)=>{
 assert.deepEqual(new Uint8Array(o.position.array.buffer),before[i].pos);
 assert.deepEqual(new Uint8Array(o.normal.array.buffer),before[i].norm);
});
for(let j=0;j<4;j++){apply(root,1.1);apply(root,1)}
wheel.forEach((o,i)=>assert.deepEqual(new Uint8Array(o.position.array.buffer),before[i].pos));
assert.throws(()=>apply(root,1.07),/Unsupported/);
const incomplete={traverse(fn){for(const x of wheel.slice(1))fn(x)}};
const original=wheel[1].position.array.slice();
assert.throws(()=>apply(incomplete,1.1),/lacks/);
assert.deepEqual(wheel[1].position.array,original);
const aliased=slots.map(mesh);
aliased[1].geometry=aliased[0].geometry;
assert.throws(()=>apply({traverse(fn){aliased.forEach(fn)}},1.1),/shared/);
console.log('source model A/B reversible, byte-exact, seven meshes only');
"""
        process = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(process.returncode, 0,
                         process.stdout + "\n" + process.stderr)


if __name__ == "__main__":
    unittest.main()
