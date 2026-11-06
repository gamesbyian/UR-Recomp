import test from "node:test";
import assert from "node:assert/strict";
import {
 SOURCE_2026_HUB_NODE,SOURCE_2026_HUB_VERTICES,SOURCE_2026_HUB_FACES,
 SOURCE_2026_HUB_MODES,experimentalAuthoredHubFace,axleLockedAuthoredHubFace,weldedAuthoredHubFace
} from "./source_hub_cover_view.mjs";

test("one authentic 2026 material and frozen reversible 3D cover proposal",()=>{
 assert.equal(SOURCE_2026_HUB_NODE,"rim_and_hub__material_4");
 assert.equal(SOURCE_2026_HUB_VERTICES,100);
 assert.equal(SOURCE_2026_HUB_FACES,196);
 assert.deepEqual(SOURCE_2026_HUB_MODES,["original","cover","axle-locked","welded"]);
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

test("axle-locked source 2026 housing exactly cancels a rotating wheel parent",()=>{
 const {vertices:original,faces}=experimentalAuthoredHubFace();
 for(const degrees of [0,11.25,24,45,90,180,345,360,720,900]){
   const locked=axleLockedAuthoredHubFace(degrees);
   assert.deepEqual(locked.faces,faces);
   assert.equal(locked.vertices.length,16);
   const theta=degrees*Math.PI/180,c=Math.cos(theta),s=Math.sin(theta);
   for(let i=0;i<original.length;i++){
     const [x,y,z]=original[i];
     const [xx,yy,zz]=locked.vertices[i];
     assert.ok(Math.abs(c*xx-s*zz-x)<1e-12);
     assert.ok(Math.abs(s*xx+c*zz-z)<1e-12);
     assert.equal(yy,y);
   }
   assert.equal(locked.original_1994_camera_or_physical_hub_recovered,false);
 }
 assert.deepEqual(axleLockedAuthoredHubFace(0).vertices,original);
 assert.notDeepEqual(axleLockedAuthoredHubFace(45).vertices,original);
 for(const bad of [NaN,Infinity,-Infinity,1081,-1081,"45",null,undefined]){
   assert.throws(()=>axleLockedAuthoredHubFace(bad));
 }
});

test("one actual 2026 source axle and cover become a single connected watertight solid",()=>{
 const source=[];
 for(const y of [-.21,.21])for(let i=0;i<50;i++){
   const a=2*Math.PI*i/50;
   source.push([.086*Math.cos(a),y,.086*Math.sin(a)]);
 }
 const {vertices:v,faces:f,...flags}=weldedAuthoredHubFace(source);
 assert.equal(flags.source_2026_hub_single_connected_solid,true);
 assert.equal(flags.original_1994_camera_or_physical_hub_recovered,false);
 assert.equal(flags.original_source_model_material_graph_changed,false);
 assert.equal(v.length,234);
 assert.equal(f.length,464);
 const edges=new Map();
 let vol6=0;
 for(const [a,b,c] of f){
   assert.equal(new Set([a,b,c]).size,3);
   assert.ok([a,b,c].every(k=>Number.isInteger(k)&&k>=0&&k<v.length));
   const P=v[a],Q=v[b],R=v[c];
   const u=Q.map((x,i)=>x-P[i]),w=R.map((x,i)=>x-P[i]);
   const cross=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]];
   assert.ok(Math.hypot(...cross)>1e-12);
   vol6+=P[0]*(Q[1]*R[2]-Q[2]*R[1])+
         P[1]*(Q[2]*R[0]-Q[0]*R[2])+P[2]*(Q[0]*R[1]-Q[1]*R[0]);
   for(const [i,j] of [[a,b],[b,c],[c,a]]){
     const key=[Math.min(i,j),Math.max(i,j)].join(',');
     edges.set(key,[...(edges.get(key)||[]),i<j?1:-1]);
   }
 }
 assert.equal(edges.size,v.length+f.length-2);
 assert.ok([...edges.values()].every(a=>a.length===2&&a[0]+a[1]===0));
 assert.ok(Math.abs(vol6/6-.07496005181)<1e-7);
 assert.deepEqual([
   Math.min(...v.map(p=>p[0])),Math.max(...v.map(p=>p[0])),
   Math.min(...v.map(p=>p[2])),Math.max(...v.map(p=>p[2]))
 ],[-.3,.22,-.37,.27]);
 for(const bad of [source.slice(0,99),source.map(p=>[p[0]*2,p[1],p[2]]),null,[]]){
   assert.throws(()=>weldedAuthoredHubFace(bad));
 }
 // This is a temporary *viewer-only* solid, not a modification to the source.
 assert.equal(source.length,100);
 assert.equal(source[0][0],.086);
});
