// ART-4K: opt-in source-world Y orientation proposals for ONE existing GLB.
// The predeclared angles come from an exploratory, non-heldout original ROM
// painted-axis coverage study. They are NOT the original game's 3D animation.
export const ROOT_LEAN_PRESETS = Object.freeze([0, -35, 10, 15, 30]);

/** Quaternion = OpenSCAD Z-up conversion * source-world-Y root lean.
 * Returns numerical components (x,y,z,w) for THREE.Quaternion.set().
 * This rotates a loaded object, not its mesh/part buffers or source asset.
 * The imported GLB source-world origin is the provisional contact pivot.
 */
export function rootLeanQuaternion(degrees, zup=true) {
  if (!ROOT_LEAN_PRESETS.includes(degrees) || typeof zup!=='boolean') {
    throw Error('unsupported experimental root lean orientation');
  }
  const radians = degrees*Math.PI/180;
  const cy=Math.cos(radians/2),sy=Math.sin(radians/2);
  if (!zup) return [0,sy,0,cy];
  const sx=Math.sin(-Math.PI/4),cx=Math.cos(-Math.PI/4);
  // Rx(-90°) * Ry(source Y lean); multiplication order is intentional.
  return [sx*cy,cx*sy,sx*sy,cx*cy];
}
