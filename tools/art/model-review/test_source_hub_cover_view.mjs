import test from "node:test";
import assert from "node:assert/strict";
import {
 SOURCE_2026_HUB_NODE,SOURCE_2026_HUB_VERTICES,SOURCE_2026_HUB_FACES,
 SOURCE_2026_HUB_MODES,experimentalAuthoredHubFace
} from "./source_hub_cover_view.mjs";

test("one authentic 2026 material and frozen reversible 3D cover proposal",()=>{
 assert.equal(SOURCE_2026_HUB_NODE,"rim_and_hub__material_4");
 assert.equal(SOURCE_2026_HUB_VERTICES,100);
 assert.equal(SOURCE_2026_HUB_FACES,196);
 assert.deepEqual(SOURCE_2026_HUB_MODES,["original","cover"]);
 const shape=experimentalAuthoredHubFace();
 assert.equal(shape.original_1994_camera_or_physical_hub_recovered,false);
 assert.equal(shape.original_source_model_material_graph_changed,false);
 assert.equal(shape.vertices.length,16);
 assert.equal(shape.faces.length,28);
 for(const [i,p] of shape.vertices.entries()){
   assert.equal(p.length,3);
   assert.ok(p.every(Number.isFinite));
   assert.equal(p[1],i<8?.18:.38);
   assert.ok(p[0]>=-.30000001&&p[0]<=.22000001);
   assert.ok(p[2]>=-.37000001&&p[2]<=.27000001);
 }
 // Separate calls must never share mutable geometry between candidates.
 const second=experimentalAuthoredHubFace();
 shape.vertices[0][0]=999;
 assert.notEqual(second.vertices[0][0],999);
 assert.deepEqual(second.vertices[0],[-.26,.18,-.37]);
});

test("authored cover is a closed, coherently oriented 2-manifold, positive volume",()=>{
 const {vertices:v,faces:f}=experimentalAuthoredHubFace();
 const edgeUse=new Map();
 let sixVolume=0;
 for(const tri of f){
   assert.equal(tri.length,3);
   assert.equal(new Set(tri).size,3);
   assert.ok(tri.every(n=>Number.isInteger(n)&&n>=0&&n<v.length));
   const [a,b,c]=tri.map(i=>v[i]);
   const u=b.map((x,i)=>x-a[i]),w=c.map((x,i)=>x-a[i]);
   const n=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]];
   assert.ok(Math.hypot(...n)>1e-10,"no degenerate triangles");
   sixVolume+=a[0]*(b[1]*c[2]-b[2]*c[1])
     +a[1]*(b[2]*c[0]-b[0]*c[2])
     +a[2]*(b[0]*c[1]-b[1]*c[0]);
   for(const [x,y] of [[tri[0],tri[1]],[tri[1],tri[2]],[tri[2],tri[0]]]){
     const k=[Math.min(x,y),Math.max(x,y)].join(":");
     const entry=edgeUse.get(k)||[];
     entry.push(x<y?1:-1);edgeUse.set(k,entry);
   }
 }
 assert.equal(edgeUse.size,42); // Euler: E=V+F-2, sphere-like single shell.
 for(const directions of edgeUse.values()){
   assert.equal(directions.length,2,"every edge has exactly two incident faces");
   assert.equal(directions[0]+directions[1],0,"opposite oriented incidence");
 }
 assert.ok(Math.abs(sixVolume/6-.06592)<1e-12,"closed authored cover signed volume");
});
