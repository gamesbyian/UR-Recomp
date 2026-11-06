// Exact one-candidate 2026 authored source-spoke cross-section control.
// Port of tools/art/experimental_spoke_blade_volume.py, NOT a recovered
// original 1994 spoke mesh, count, artist camera or approved HD art.
export const SOURCE_2026_SPOKE_NODE="rim_and_hub__material_2";
export const SOURCE_2026_SPOKE_VERTICES=1788;
export const SOURCE_2026_BLADE_FACTOR=2;
const HALF_TURN=Math.PI, PITCH=2*Math.PI/8, OFFSET=11*Math.PI/180;
const ROOT=.12, FULL=.72;
export function broadenOriginal2026Spoke(x,y,z){
 if(![x,y,z].every(v=>typeof v==="number"&&Number.isFinite(v)))
   throw Error("finite 2026 source spoke XYZ required");
 const r=Math.hypot(x,z);
 if(r<=ROOT)return [x,y,z];
 const theta=Math.atan2(x,z);
 // Python round nearest spoke center: no tie occurs in the fixed GLB.
 const axis=OFFSET+Math.round((theta-OFFSET)/PITCH)*PITCH;
 const delta=Math.atan2(Math.sin(theta-axis),Math.cos(theta-axis));
 const progress=Math.min(1,Math.max(0,(r-ROOT)/(FULL-ROOT)));
 const phi=axis+delta*(1+(SOURCE_2026_BLADE_FACTOR-1)*progress*progress);
 return [r*Math.sin(phi),y,r*Math.cos(phi)];
}
export const SOURCE_2026_BLADE_MODES=Object.freeze(["original","blade"]);
