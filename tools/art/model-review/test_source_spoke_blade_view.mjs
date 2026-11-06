import test from "node:test";
import assert from "node:assert/strict";
import {SOURCE_2026_SPOKE_NODE,SOURCE_2026_SPOKE_VERTICES,
 SOURCE_2026_BLADE_FACTOR,SOURCE_2026_BLADE_MODES,broadenOriginal2026Spoke}
 from "./source_spoke_blade_view.mjs";

test("one source-owned 2026 eight-spoke material and bounded original geometry",()=>{
 assert.equal(SOURCE_2026_SPOKE_NODE,"rim_and_hub__material_2");
 assert.equal(SOURCE_2026_SPOKE_VERTICES,1788);
 assert.equal(SOURCE_2026_BLADE_FACTOR,2);
 assert.deepEqual(SOURCE_2026_BLADE_MODES,["original","blade"]);
 const theta=11*Math.PI/180,r=.7,dist=.02,y=-.025;
 const center=[r*Math.sin(theta),y,r*Math.cos(theta)];
 const outside=[r*Math.sin(theta+dist),y,r*Math.cos(theta+dist)];
 const oldWidth=Math.hypot(center[0]-outside[0],center[2]-outside[2]);
 const result=broadenOriginal2026Spoke(...outside);
 const newWidth=Math.hypot(center[0]-result[0],center[2]-result[2]);
 assert.ok(newWidth>oldWidth);
 assert.ok(Math.abs(Math.hypot(result[0],result[2])-r)<1e-12);
 assert.equal(result[1],y);
 for(const source of [[0,0,0],[.04,-.05,.04],[0,.04,.06]]){
  assert.deepEqual(broadenOriginal2026Spoke(...source),source);
 }
 for(const bad of [[NaN,0,0],[0,Infinity,0],[0,0,null],[0,0,"1"]])
  assert.throws(()=>broadenOriginal2026Spoke(...bad),/finite/);
});
test("eight-spoke blade transformation remains rotationally symmetric at every 45 degrees",()=>{
 const x=.65*Math.sin(14*Math.PI/180), z=.65*Math.cos(14*Math.PI/180);
 const a=broadenOriginal2026Spoke(x,-.02,z);
 for(let k=1;k<8;k++){
  const t=k*Math.PI/4;
  const xp=x*Math.cos(t)+z*Math.sin(t);
  const zp=z*Math.cos(t)-x*Math.sin(t);
  const b=broadenOriginal2026Spoke(xp,-.02,zp);
  assert.ok(Math.abs(b[0]-(a[0]*Math.cos(t)+a[2]*Math.sin(t)))<1e-12);
  assert.ok(Math.abs(b[2]-(a[2]*Math.cos(t)-a[0]*Math.sin(t)))<1e-12);
  assert.equal(b[1],a[1]);
 }
});
