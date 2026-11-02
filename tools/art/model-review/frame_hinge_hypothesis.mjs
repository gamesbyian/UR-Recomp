// ART-4K: one existing GLB, source-world-Y axle-centred fork/saddle control.
// No original 1994 motion, camera, joint limits or owner likeness claimed.
export const FRAME_HINGE_PRESETS=Object.freeze([0,-40,-20,20,40]);

/** Column-major 4x4 matrix for THREE.Matrix4.fromArray().
 * Parent code composes axleMatrix * R * inverse(axleMatrix), then applies
 * the result to each ORIGINAL fork/saddle parent matrix, never cumulatively.
 */
export function frameHingeSourceRotation(degrees){
 if(typeof degrees!=='number'||!Number.isFinite(degrees)||!FRAME_HINGE_PRESETS.includes(degrees)){
  throw Error('unsupported experimental frame hinge angle');
 }
 const theta=degrees*Math.PI/180,c=Math.cos(theta),s=Math.sin(theta);
 return [c,0,-s,0, 0,1,0,0, s,0,c,0, 0,0,0,1];
}
