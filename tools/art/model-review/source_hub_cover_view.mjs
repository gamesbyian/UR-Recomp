// One frozen *2026 authored model* experiment, not 1994 recovered geometry.
// Same X/Z eight-chamfer near-side volume as experimental #3182.
// Traced 1994 printed p15 exposed face is two-dimensional and uncalibrated.
export const SOURCE_2026_HUB_NODE="rim_and_hub__material_4";
export const SOURCE_2026_HUB_VERTICES=100;
export const SOURCE_2026_HUB_FACES=196;
export const SOURCE_2026_HUB_MODES=Object.freeze(["original","cover"]);
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
