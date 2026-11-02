// Reversible 2026 source-rig wheel/crank phase study, NOT original 1994 timing.
export const SOURCE_SHA="e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984";
export const PEDAL_PHASE=Object.freeze({upright:18,pedal:88,wheelie:44,stunt:120,bank:150});
export function sourcePhaseDelta(pose,sha){
 if(typeof pose!=="string"||!Object.hasOwn(PEDAL_PHASE,pose)||sha!==SOURCE_SHA)
  throw Error("source-owned direct-drive phase unavailable");
 return PEDAL_PHASE[pose]-18;
}
// Column-major THREE.Matrix4: OpenSCAD rotate([0,-delta,0]) in source Z-up.
export function sourceDriveMatrix(pose,sha){
 const t=sourcePhaseDelta(pose,sha)*Math.PI/180,c=Math.cos(t),s=Math.sin(t);
 return [c,0,s===0?0:s,0, 0,1,0,0, s===0?0:-s,0,c,0, 0,0,0,1];
}
