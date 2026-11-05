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


// Additional source-only parameter: two crank revolutions over normalized ride
// time. Exactly 64 interactive steps expose 11.25° increments, avoiding the
// older nine-sample grid's eight-spoke 45° rotational symmetry alias.
export const CRANK_STEPS=64;
export function sourceCrankDegrees(step){
 if(typeof step!=='number'||!Number.isInteger(step)||step<0||step>CRANK_STEPS)
  throw Error("unsupported source experimental crank step");
 return 720*step/CRANK_STEPS;
}
function matrixAtDegrees(degrees){
 // Canonicalize complete cycles to exact identity, preventing floating-point
 // drift at 360° and 720° when restoring parent TRS in the browser.
 const d=((degrees%360)+360)%360;
 if(d===0)return [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1];
 const t=d*Math.PI/180,c=Math.cos(t),s=Math.sin(t);
 return [c,0,s,0, 0,1,0,0, -s,0,c,0, 0,0,0,1];
}
export function sourceCrankMatrix(step){
 return matrixAtDegrees(sourceCrankDegrees(step));
}
export function sourceWheelPoseMatrix(pose,sha,step){
 return matrixAtDegrees(sourcePhaseDelta(pose,sha)+sourceCrankDegrees(step));
}
