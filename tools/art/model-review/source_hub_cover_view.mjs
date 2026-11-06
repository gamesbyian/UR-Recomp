// One frozen *2026 authored model* experiment, not 1994 recovered geometry.
// Same X/Z eight-chamfer near-side volume as experimental #3182.
// Traced 1994 printed p15 exposed face is two-dimensional and uncalibrated.
export const SOURCE_2026_HUB_NODE="rim_and_hub__material_4";
export const SOURCE_2026_HUB_VERTICES=100;
export const SOURCE_2026_HUB_FACES=196;
export const SOURCE_2026_HUB_MODES=Object.freeze(["original","cover","axle-locked"]);
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
