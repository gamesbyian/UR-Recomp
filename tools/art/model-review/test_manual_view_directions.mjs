import test from "node:test";
import assert from "node:assert/strict";
import {CAMERA_VIEW_PRESETS,cameraViewDirection} from "./manual_view_directions.mjs";

test("retain five original camera views and add two truly 3D print-inspired angles",()=>{
 assert.deepEqual(CAMERA_VIEW_PRESETS.map(x=>x.id),
  ["side","reverse","front","back","top","print-fork","print-hub"]);
 for(const preset of CAMERA_VIEW_PRESETS){
  const view=cameraViewDirection(preset.id);
  assert.equal(view.camera_is_original_1994_rendering,false);
  assert.equal(view.model_mesh_geometry_unchanged,true);
  assert.ok(Math.abs(Math.hypot(...view.vector)-1)<1e-12);
  assert.ok(view.vector.every(Number.isFinite));
 }
 const front=cameraViewDirection("print-fork");
 assert.equal(front.printedPage,14);
 assert.ok(front.vector[0]>.9);
 assert.ok(front.vector[1]>0);
 const underside=cameraViewDirection("print-hub");
 assert.equal(underside.printedPage,15);
 assert.ok(underside.vector[1]<-.3);
 assert.ok(underside.vector[2]>.5);
 assert.notDeepEqual(front.vector,underside.vector);
 for(const bad of [undefined,null,{},0,"original","manual-1994-true-camera"]){
  assert.throws(()=>cameraViewDirection(bad),/unknown/);
 }
});
