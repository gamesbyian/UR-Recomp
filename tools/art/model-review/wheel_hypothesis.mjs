// Read-only 2026 source-GLB width experiment for the ONE existing model viewer.
// Do not confuse this with recovered original 1994 3D geometry or art approval.
// Exact tire (2) + rim/hub (5) material child meshes; all other nodes untouched.
const PART_SLOTS = Object.freeze([
  'tire__material_0', 'tire__material_1',
  'rim_and_hub__material_0', 'rim_and_hub__material_1',
  'rim_and_hub__material_2', 'rim_and_hub__material_3',
  'rim_and_hub__material_4'
]);
export const WHEEL_HYPOTHESIS_FACTORS = Object.freeze([1, 1.1]);
const ORIGINAL = new WeakMap();

function attributeView(attribute) {
  const view=attribute?.array ?? attribute?.data?.array;
  return ArrayBuffer.isView(view) ? view : null;
}
function overlaps(a,b) {
  return a.buffer===b.buffer &&
    a.byteOffset < b.byteOffset+b.byteLength &&
    b.byteOffset < a.byteOffset+a.byteLength;
}
function attributesOf(geometry) {
  const entries=Object.entries(geometry?.attributes ?? {});
  for (const role of ['position','normal']) {
    if (!entries.some(([name])=>name===role)) {
      const attribute=geometry?.getAttribute?.(role);
      if (attribute) entries.push([role,attribute]);
    }
  }
  const index=geometry?.getIndex?.() ?? geometry?.index;
  if (index) entries.push(['index',index]);
  return entries;
}
/** Mutate only tire/rim X of a loaded, named GLB mesh, never its source bytes.
 * The original vertex and normal Float32 data is cached per BufferGeometry,
 * and baseline reversion restores it bit-for-bit even after many toggles.
 */
export function applyWheelWidthHypothesis(root, factor) {
  if (!root || typeof root.traverse !== 'function' ||
      !WHEEL_HYPOTHESIS_FACTORS.includes(factor)) {
    throw Error('Unsupported experimental wheel factor or model');
  }
  const meshes = new Map(), allGeometries = [];
  root.traverse(object => {
    if (object.geometry) allGeometries.push(object);
    if (object.isMesh && PART_SLOTS.includes(object.name)) {
      if (meshes.has(object.name)) throw Error('Duplicated named wheel material node');
      meshes.set(object.name, object);
    }
  });
  if (PART_SLOTS.some(name => !meshes.has(name)) || meshes.size !== PART_SLOTS.length) {
    throw Error('This model lacks the required seven source-owned wheel/rim materials');
  }
  const geometrySet = new Set();
  const checked = [];
  for (const name of PART_SLOTS) {
    const geometry = meshes.get(name).geometry;
    if (!geometry || geometrySet.has(geometry)) {
      throw Error('Wheel material uses shared/missing geometry');
    }
    geometrySet.add(geometry);
    const position = geometry.getAttribute?.('position');
    const normal = geometry.getAttribute?.('normal');
    if (!position || !normal || position.itemSize !== 3 || normal.itemSize !== 3 ||
        position.count !== normal.count || position.count <= 0 ||
        !position.array || !normal.array ||
        position.array.length !== position.count * 3 ||
        normal.array.length !== normal.count * 3) {
      throw Error('Model wheel geometry has incompatible position/normal data');
    }
    let original = ORIGINAL.get(geometry);
    if (!original) {
      original = {positions: Float32Array.from(position.array),
                  normals: Float32Array.from(normal.array)};
    }
    if (original.positions.length !== position.array.length ||
        original.normals.length !== normal.array.length ||
        !original.positions.every(Number.isFinite) ||
        !original.normals.every(Number.isFinite)) {
      throw Error('Nonfinite or changed experimental wheel geometry');
    }
    if (factor !== 1) {
      for (let i = 0; i < original.normals.length; i += 3) {
        const x = original.normals[i] / factor;
        const y = original.normals[i+1], z = original.normals[i+2];
        const magnitude = Math.hypot(x, y, z);
        if (!(magnitude > 0) || !Number.isFinite(magnitude)) {
          throw Error('Invalid experimental wheel normal');
        }
      }
    }
    checked.push({name, geometry, position, normal, original});
  }
  // Two distinct BufferGeometry objects may still share attribute storage.
  // Also a non-wheel part may point to a wheel's *same* BufferGeometry.
  // Refuse all overlapping POSITION/NORMAL buffers across every GLB object,
  // including COLOR_0, indices, interleaved or other-named attributes.
  const mutations=checked.flatMap(({name, position, normal}) => [
    {object:meshes.get(name), role:'position', attribute:position, view:attributeView(position)},
    {object:meshes.get(name), role:'normal', attribute:normal, view:attributeView(normal)}
  ]);
  if (mutations.some(m=>!m.view)) throw Error('Wheel attribute data is not independently backed');
  for (const object of allGeometries) {
    for (const [role, attribute] of attributesOf(object.geometry)) {
      const view=attributeView(attribute);
      if (!view) throw Error('Cannot prove independent geometry attribute storage');
      for (const m of mutations) {
        if (overlaps(view,m.view) &&
            !(object===m.object && role===m.role && attribute===m.attribute)) {
          throw Error('Wheel attribute bytes overlap a non-target model attribute');
        }
      }
    }
  }
  // All 7 materials must pass preflight before changing even one vertex.
  for (const {geometry, position, normal, original} of checked) {
    ORIGINAL.set(geometry, original);
    for (let i = 0; i < position.count; i++) {
      const k = i * 3;
      position.setXYZ(i, original.positions[k] * factor,
                      original.positions[k+1], original.positions[k+2]);
      if (factor === 1) {
        normal.setXYZ(i, original.normals[k],
                      original.normals[k+1], original.normals[k+2]);
      } else {
        const x = original.normals[k] / factor;
        const y = original.normals[k+1];
        const z = original.normals[k+2];
        const magnitude = Math.hypot(x, y, z);
        if (!(magnitude > 0) || !Number.isFinite(magnitude)) {
          throw Error('Invalid experimental wheel normal');
        }
        normal.setXYZ(i, x/magnitude, y/magnitude, z/magnitude);
      }
    }
    position.needsUpdate = true;
    normal.needsUpdate = true;
    geometry.computeBoundingBox?.();
    geometry.computeBoundingSphere?.();
  }
  return {modifiedMaterialMeshes: PART_SLOTS.length,
          wheelAndRimLocalXFactor: factor,
          sourceGLBModified: false,
          original1994LikenessApproved: false};
}
