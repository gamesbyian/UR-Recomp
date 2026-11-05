// Optional, read-only model-review measurement evidence, no vendor dependencies.
// Browser and Node test compatible. Never infer authentic 1994 sprite-to-GLB pose.
export const POSES = Object.freeze(['upright','pedal','wheelie','stunt','bank']);
export const SCHEMA = 'UR-RACER-MODEL-REVIEW-MEASUREMENT-SIDECAR/1';
const sha = x => typeof x === 'string' && /^[0-9a-f]{64}$/.test(x);
const gitsha = x => typeof x === 'string' && /^[0-9a-f]{40}$/.test(x);
const own = (obj,key) => Object.prototype.hasOwnProperty.call(obj,key);
const fixed = flags => flags.every(([a,b]) => a === b);
export function digestText(text, cryptoEngine = globalThis.crypto) {
  if (!cryptoEngine?.subtle) return Promise.reject(Error('SHA-256 unavailable in this browser'));
  const data = new TextEncoder().encode(text);
  return cryptoEngine.subtle.digest('SHA-256',data).then(bytes =>
    [...new Uint8Array(bytes)].map(x => x.toString(16).padStart(2,'0')).join(''));
}
export async function validateMeasurements(measurements, {manifest, sprites, manifestRaw, spritesRaw}, hash = digestText) {
  const m=measurements, model=manifest, rail=sprites;
  if (!m || typeof m !== 'object' || Array.isArray(m) || m.schema!==SCHEMA) throw Error('Unknown measurement schema');
  if (!model || model.schema!=='ur-racer-model-review/1' || !model.model_url) throw Error('No verified published model');
  if (!rail || rail.schema!=='ur-racer-original-sprite-reference/1' || !Array.isArray(rail.frames) || rail.sprite_3d_pose_mapping_verified!==false) throw Error('Original reference rail unavailable');
  if (typeof manifestRaw!=='string' || typeof spritesRaw!=='string') throw Error('Exact viewer source JSON bytes required');
  if (!sha(m.viewer_manifest_sha256) || !sha(m.viewer_sprite_rail_sha256) ||
      m.viewer_manifest_sha256!==(await hash(manifestRaw)) ||
      m.viewer_sprite_rail_sha256!==(await hash(spritesRaw))) throw Error('Stale or mismatched viewer source evidence');
  if (!gitsha(m.source_model_commit) || m.source_model_commit!==model.source_commit ||
      !sha(m.source_model_scad_sha256) || m.source_model_scad_sha256!==model.source_model_sha256 ||
      !sha(m.source_rom_sha256) || m.source_rom_sha256!==rail.source_sha256 ||
      !sha(m.source_registry_sha256) || !sha(m.camera_manifest_sha256)) throw Error('Model, ROM or camera provenance differs');
  if (!fixed([
    [m.camera_status,'provisional'],
    [m.source_registration_mode,'original-pixel-verified-contact-anchor'],
    [m.source_anchor_is_physical_ground_contact,false],
    [m.source_to_experimental_model_pose_mapping_verified,false],
    [m.recovered_1994_3d_camera_verified,false],
    [m.independent_heldout_family_tested,false],
    [m.owner_character_likeness_approved,false],
    [m.shipping_art_approved,false],
    [m.margin_is_an_authentic_pose_probability,false],
    [model.likeness_approved,false],
    [model.source_sprite_pose_registration,false]
  ])) throw Error('Unsupported authentic-pose or likeness claim');
  if (!m.source_pose_glb_sha256 || !model.poses ||
      Object.keys(m.source_pose_glb_sha256).length!==5 || Object.keys(model.poses).length!==5 ||
      !POSES.every(p=>own(m.source_pose_glb_sha256,p)&&own(model.poses,p)&&
         sha(m.source_pose_glb_sha256[p])&&m.source_pose_glb_sha256[p]===model.poses[p].sha256)) throw Error('Stale or incomplete five-GLB model');
  if (m.distinct_original_source_binary_silhouette_count!==10 || m.experimental_glb_pose_count!==5 ||
      m.original_frame_observations!==32 ||
      !Array.isArray(m.source_shape_measurements) || m.source_shape_measurements.length!==10 ||
      !Array.isArray(rail.frames) || rail.frames.length!==32) throw Error('Unexpected original-source observation census');
  const frames=new Map();
  for(const frame of rail.frames) {
    const key=frame.player+':'+frame.guest_frame;
    if(!['p1','p2'].includes(frame.player) || !Number.isInteger(frame.guest_frame) ||
        frame.guest_frame<1205 || frame.guest_frame>1220 ||
        !sha(frame.sha256) || typeof frame.representation_id!=='string' ||
        !frame.representation_id || frames.has(key)) throw Error('Invalid original-source rail identity');
    frames.set(key,frame);
  }
  const used=new Set(), groups=new Set(), totals=Object.fromEntries(POSES.map(p=>[p,0])), wins=Object.fromEntries(POSES.map(p=>[p,0]));
  let gapTotal=0;
  for(const row of m.source_shape_measurements) {
    if(!sha(row.original_binary_mask_sha256) || groups.has(row.original_binary_mask_sha256)) throw Error('Duplicate source silhouette');
    groups.add(row.original_binary_mask_sha256);
    if(!Array.isArray(row.source_frames)||!row.source_frames.length||!row.unpaired_scores ||
       Object.keys(row.unpaired_scores).length!==5) throw Error('Incomplete source silhouette group');
    for(const f of row.source_frames) {
      const key=f.player+':'+f.guest_frame, original=frames.get(key);
      if(!original || used.has(key) || f.representation_id!==original.representation_id ||
         f.original_png_sha256!==original.sha256) throw Error('Source sprite identity or PNG hash changed');
      used.add(key);
    }
    const anchor=row.registered_original_contact_x2_y2, shift=row.source_logical_translation_from_witness_xy;
    if(!Array.isArray(anchor)||!Array.isArray(shift)||anchor.length!==2||shift.length!==2 ||
       !anchor.every(Number.isInteger)||!shift.every(Number.isInteger) ||
       anchor[0]-67!==2*shift[0]||anchor[1]-76!==2*shift[1]) throw Error('Source anchor registration changed');
    const ranked=[];
    for(const p of POSES) {
      const v=row.unpaired_scores[p];
      if(!v || typeof v.silhouette_iou!=='number' || !Number.isFinite(v.silhouette_iou) ||
         v.silhouette_iou<0 || v.silhouette_iou>1 ||
         typeof v.boundary_chamfer_physical_px!=='number' || !Number.isFinite(v.boundary_chamfer_physical_px) ||
         v.boundary_chamfer_physical_px<0 || v.boundary_chamfer_physical_px>100) throw Error('Invalid unpaired research metric');
      totals[p]+=v.silhouette_iou;
      ranked.push({p,iou:v.silhouette_iou,chamfer:v.boundary_chamfer_physical_px});
    }
    ranked.sort((a,b)=>b.iou-a.iou||a.chamfer-b.chamfer||a.p.localeCompare(b.p));
    const margin=Math.round((ranked[0].iou-ranked[1].iou)*1e8)/1e8;
    if(row.highest_iou_experimental_pose!==ranked[0].p ||
       row.runner_up_iou_experimental_pose!==ranked[1].p ||
       row.first_minus_second_unpaired_iou_margin!==margin ||
       row.highest_iou_pose_is_an_authenticated_original_pose!==false ||
       row.margin_is_pose_identity_confidence!==false) throw Error('Invalid pose ranking claim');
    gapTotal+=margin;wins[ranked[0].p]++;
  }
  if(used.size!==frames.size) throw Error('Source observation census incomplete');
  if(!m.equal_original_mask_weighted_mean_silhouette_iou || !m.experimental_pose_highest_iou_counts) throw Error('Missing source-shape-weighted summary');
  for(const p of POSES) {
    if(m.equal_original_mask_weighted_mean_silhouette_iou[p]!==Math.round(totals[p]/10*1e8)/1e8 ||
       m.experimental_pose_highest_iou_counts[p]!==wins[p]) throw Error('Inconsistent source-shape-weighted result');
  }
  if(m.mean_first_minus_second_unpaired_iou_margin!==Math.round(gapTotal/10*1e8)/1e8) throw Error('Inconsistent ambiguity margin');
  return m; // Never mutate a viewer model, original source art, or UI state.
}
export function measurementForFrame(measurements,player,guestFrame) {
  if(!measurements) return null;
  return measurements.source_shape_measurements.find(row=>
    row.source_frames.some(frame=>frame.player===player&&frame.guest_frame===guestFrame))||null;
}
