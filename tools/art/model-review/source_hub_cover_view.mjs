// One frozen *2026 authored model* experiment, not 1994 recovered geometry.
// Same X/Z eight-chamfer near-side volume as experimental #3182.
// Traced 1994 printed p15 exposed face is two-dimensional and uncalibrated.
export const SOURCE_2026_HUB_NODE="rim_and_hub__material_4";
export const SOURCE_2026_HUB_VERTICES=100;
export const SOURCE_2026_HUB_FACES=196;
export const SOURCE_2026_HUB_MODES=Object.freeze(["original","cover","axle-locked","welded"]);
export function experimentalAuthoredHubFace(){
 const hw=.26,hh=.32,b=.04,centerX=-.04,centerZ=-.05;
 const outline=[
  [-hw+b,-hh],[hw-b,-hh],[hw,-hh+b],[hw,hh-b],
  [hw-b,hh],[-hw+b,hh],[-hw,hh-b],[-hw,-hh+b]];
 const vertices=[];
 for(const y of [.18,.38])
  for(const [x,z] of outline)vertices.push([centerX+x,y,centerZ+z]);
 const faces=[];
 for(let i=1;i<=6;i++){
  faces.push([0,i,i+1],[8,8+i+1,8+i]);
 }
 for(let i=0;i<8;i++){
  const j=(i+1)%8;
  faces.push([i,8+j,j],[i,8+i,8+j]);
 }
 if(vertices.length!==16||faces.length!==28)
  throw Error("single fixed 2026 hub-cover source geometry changed");
 return {vertices,faces,
  original_1994_camera_or_physical_hub_recovered:false,
  original_source_model_material_graph_changed:false};
}

/** Stationary-axle kinematic counterfactual of the SAME 2026 dark 3D volume.
 * Wheel parents in the verified OpenSCAD source apply Ry(-phase), so pre-rotate
 * the new shell by Ry(+phase) locally. Only the new 16 authored vertices move:
 * every original source vertex and all sixteen material IDs remain immutable.
 * The 1994 source hub joint/camera are NOT recovered from the print/manual.
 */
export function axleLockedAuthoredHubFace(wheelDegrees){
 if(typeof wheelDegrees!=='number'||!Number.isFinite(wheelDegrees)||
    Math.abs(wheelDegrees)>1080)
   throw Error('verified 2026 wheel-phase degrees required for axle-locked cover');
 const shape=experimentalAuthoredHubFace();
 const degrees=((wheelDegrees%360)+360)%360;
 if(degrees===0)return shape;
 const a=degrees*Math.PI/180,c=Math.cos(a),s=Math.sin(a);
 return {...shape,vertices:shape.vertices.map(([x,y,z])=>
   [c*x+s*z,y,-s*x+c*z])};
}

/** Authoring quality: ONE source-verified 2026 axle sleeve plus dark casing.
 * Pure 3D topology experiment. The 1994 original artist hub is UNKNOWN.
 * The existing 2026 axle is a 50-section Y cylinder (100 vertices). Match
 * all fifty azimuths plus the exact eight source-authored beveled corners,
 * and eliminate the two overlapping closed solids by sewing one annulus.
 */
export function weldedAuthoredHubFace(sourceVertices){
 if(!Array.isArray(sourceVertices)||sourceVertices.length!==100||
    !sourceVertices.every(p=>Array.isArray(p)&&p.length===3&&p.every(Number.isFinite)))
   throw Error('exact original 2026 source hub cylinder required');
 const levels=[...new Set(sourceVertices.map(p=>Number(p[1].toFixed(5))))].sort((a,b)=>a-b);
 if(levels.length!==2||levels[0]!==-.21||levels[1]!==.21)
   throw Error('exact source 2026 hub Y limits changed');
 const lower=sourceVertices.filter(p=>Math.abs(p[1]-levels[0])<1e-5);
 const upper=sourceVertices.filter(p=>Math.abs(p[1]-levels[1])<1e-5);
 if(lower.length!==50||upper.length!==50)
   throw Error('exact 50-section original 2026 axle sleeve required');
 const radii=lower.map(([x,,z])=>Math.hypot(x,z));
 if(radii.some(r=>Math.abs(r-.086)>2e-5))
   throw Error('source 2026 hub radius changed');
 const radius=radii.reduce((a,b)=>a+b,0)/radii.length;
 const polygon=experimentalAuthoredHubFace().vertices.slice(0,8).map(([x,,z])=>[x,z]);
 const cross=(a,b)=>a[0]*b[1]-a[1]*b[0];
 const ray=theta=>{
   const d=[Math.cos(theta),Math.sin(theta)];
   const hits=[];
   for(let i=0;i<8;i++){
     const a=polygon[i],b=polygon[(i+1)%8],e=[b[0]-a[0],b[1]-a[1]];
     const det=cross(d,e);
     if(Math.abs(det)<1e-12)continue;
     const r=cross(a,e)/det,t=cross(a,d)/det;
     if(r>0&&t>=-1e-8&&t<=1+1e-8)hits.push(r);
   }
   if(hits.length===0)throw Error('2026 cover polygon ray failed');
   const r=Math.min(...hits);return [r*d[0],r*d[1]];
 };
 const roundAngle=theta=>Math.round(theta*1e12)/1e12;
 const angles=[...new Set([
   ...lower.map(([x,,z])=>roundAngle(Math.atan2(z,x))),
   ...polygon.map(([x,z])=>roundAngle(Math.atan2(z,x)))
 ])].sort((a,b)=>a-b);
 if(angles.length!==58)throw Error('expected 50 original hub rays plus 8 polygon corners');
 const inner=(theta,y)=>[radius*Math.cos(theta),y,radius*Math.sin(theta)];
 const outer=(theta,y)=>{const [x,z]=ray(theta);return [x,y,z]};
 const vertices=[
   ...angles.map(a=>inner(a,levels[0])),
   ...angles.map(a=>inner(a,.18)),
   ...angles.map(a=>outer(a,.18)),
   ...angles.map(a=>outer(a,.38)),
   [0,levels[0],0],[-.04,.38,-.05],
 ];
 const faces=[],n=angles.length;
 for(let band=0;band<3;band++){
   const bottom=band*n,top=(band+1)*n;
   for(let i=0;i<n;i++){
     const j=(i+1)%n;
     faces.push([bottom+i,top+i,bottom+j],[top+i,top+j,bottom+j]);
   }
 }
 for(let i=0;i<n;i++){
   const j=(i+1)%n;
   faces.push([4*n,i,j],[4*n+1,3*n+j,3*n+i]);
 }
 if(vertices.length!==234||faces.length!==464)
   throw Error('source-bound 2026 single connected housing topology changed');
 return {vertices,faces,
  original_1994_camera_or_physical_hub_recovered:false,
  original_source_model_material_graph_changed:false,
  source_2026_hub_single_connected_solid:true};
}
