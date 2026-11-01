#!/usr/bin/env node
import assert from 'node:assert/strict';
import {createHash, webcrypto} from 'node:crypto';
import {test} from 'node:test';
import {POSES,SCHEMA,validateMeasurements,measurementForFrame,digestText} from './measurement_overlay.mjs';
const sha=x=>createHash('sha256').update(x).digest('hex');
const json=x=>JSON.stringify(x)+'\n';
const roots=()=> {
 const frames=[];
 for(const p of ['p1','p2']) for(let n=1205;n<=1220;n++)
  frames.push({player:p,guest_frame:n,representation_id:p+'-'+n,sha256:sha(p+'-'+n),image:'sprites/a.png'});
 const sprites={schema:'ur-racer-original-sprite-reference/1',source_sha256:'e'.repeat(64),
  sprite_3d_pose_mapping_verified:false,frames};
 const poses=Object.fromEntries(POSES.map((p,i)=>[p,{url:'assets/'+p+'.glb',sha256:String(i+1).padStart(64,'0')}]));
 const manifest={schema:'ur-racer-model-review/1',model_url:'assets/upright.glb',poses,
  source_commit:'a'.repeat(40),source_model_sha256:'b'.repeat(64),
  likeness_approved:false,source_sprite_pose_registration:false};
 const raw={manifestRaw:json(manifest),spritesRaw:json(sprites)};
 const rows=[], totals=Object.fromEntries(POSES.map(p=>[p,0]));
 for(let j=0;j<10;j++){
  const observations=frames.slice(j*3,j===9?32:(j+1)*3);
  const scores={};
  for(let k=0;k<5;k++){const p=POSES[k],iou=Number((.2+j*.01+k*.04).toFixed(8));
   scores[p]={silhouette_iou:iou,boundary_chamfer_physical_px:Number((2-k*.1).toFixed(8))};totals[p]+=iou;}
  rows.push({original_binary_mask_sha256:String(j+10).padStart(64,'0'),
   source_frames:observations.map(f=>({player:f.player,guest_frame:f.guest_frame,
    representation_id:f.representation_id,original_png_sha256:f.sha256})),
   registered_original_contact_x2_y2:[67+2*(j%3),76],source_logical_translation_from_witness_xy:[j%3,0],
   unpaired_scores:scores,highest_iou_experimental_pose:'bank',runner_up_iou_experimental_pose:'stunt',
   first_minus_second_unpaired_iou_margin:.04,margin_is_pose_identity_confidence:false,
   highest_iou_pose_is_an_authenticated_original_pose:false});
 }
 const report={schema:SCHEMA,viewer_manifest_sha256:sha(raw.manifestRaw),viewer_sprite_rail_sha256:sha(raw.spritesRaw),
  source_model_commit:manifest.source_commit,source_model_scad_sha256:manifest.source_model_sha256,
  source_pose_glb_sha256:Object.fromEntries(POSES.map(p=>[p,poses[p].sha256])),
  source_rom_sha256:sprites.source_sha256,source_registry_sha256:'c'.repeat(64),camera_manifest_sha256:'d'.repeat(64),
  camera_status:'provisional',source_registration_mode:'original-pixel-verified-contact-anchor',
  source_anchor_is_physical_ground_contact:false,source_to_experimental_model_pose_mapping_verified:false,
  recovered_1994_3d_camera_verified:false,independent_heldout_family_tested:false,owner_character_likeness_approved:false,
  shipping_art_approved:false,margin_is_an_authentic_pose_probability:false,
  distinct_original_source_binary_silhouette_count:10,experimental_glb_pose_count:5,original_frame_observations:32,
  source_shape_measurements:rows,experimental_pose_highest_iou_counts:Object.fromEntries(POSES.map(p=>[p,p==='bank'?10:0])),
  equal_original_mask_weighted_mean_silhouette_iou:Object.fromEntries(POSES.map(p=>[p,Math.round(totals[p]/10*1e8)/1e8])),
  mean_first_minus_second_unpaired_iou_margin:.04};
 return {report,manifest,sprites,raw};
};
const check=({report,manifest,sprites,raw})=>validateMeasurements(report,{manifest,sprites,...raw},
 data=>Promise.resolve(sha(data)));
test('real SHA primitive hashes exact serialized JSON, browser and Node compatible',async()=>{
 assert.equal(await digestText('test',webcrypto),sha('test'));
});
test('valid mock research evidence remains unpaired and keyed by source frame',async()=>{
 const fixture=roots();
 assert.equal(await check(fixture),fixture.report);
 assert.equal(measurementForFrame(fixture.report,'p1',1205).source_frames[0].guest_frame,1205);
 assert.equal(measurementForFrame(fixture.report,'p3',1205),null);
 assert.equal(measurementForFrame(null,'p1',1205),null);
});
test('source manifest and sprite rail SHA change are fatal, even when claims are self-consistent',async()=>{
 const f=roots();f.raw.manifestRaw=json({...f.manifest,version:'changed'});
 await assert.rejects(check(f),/Stale or mismatched viewer/);
 const g=roots();g.sprites.frames[0].representation_id='swapped';
 await assert.rejects(check(g),/Source sprite identity/);
});
test('source ROM/model/pose hash and false approval claims cannot be forged',async()=>{
 for(const alteration of [
  x=>x.report.source_rom_sha256='f'.repeat(64),
  x=>x.report.source_pose_glb_sha256.bank='f'.repeat(64),
  x=>x.report.shipping_art_approved=true,
  x=>x.report.source_to_experimental_model_pose_mapping_verified=true,
  x=>x.report.camera_status='source-calibrated',
  x=>x.report.source_anchor_is_physical_ground_contact=true,
 ]){
  const f=roots();alteration(f);await assert.rejects(check(f));
 }
});
test('missing, repeated or misidentified original frame cannot vote twice',async()=>{
 for(const alteration of [
  x=>x.report.source_shape_measurements[0].source_frames.pop(),
  x=>x.report.source_shape_measurements[1].source_frames[0]=x.report.source_shape_measurements[0].source_frames[0],
  x=>x.report.source_shape_measurements[1].original_binary_mask_sha256=x.report.source_shape_measurements[0].original_binary_mask_sha256,
  x=>x.report.source_shape_measurements[0].source_frames[0].original_png_sha256='f'.repeat(64)
 ]){const f=roots();alteration(f);await assert.rejects(check(f));}
});
test('rank margins, means and IOU bounds must be independently recomputed',async()=>{
 for(const alteration of [
  x=>x.report.source_shape_measurements[0].highest_iou_experimental_pose='wheelie',
  x=>x.report.source_shape_measurements[0].first_minus_second_unpaired_iou_margin=.99,
  x=>x.report.source_shape_measurements[0].unpaired_scores.bank.silhouette_iou=1.1,
  x=>x.report.source_shape_measurements[0].unpaired_scores.bank.boundary_chamfer_physical_px=-1,
  x=>x.report.experimental_pose_highest_iou_counts.bank=9,
  x=>x.report.equal_original_mask_weighted_mean_silhouette_iou.bank=0.99,
  x=>x.report.mean_first_minus_second_unpaired_iou_margin=.5,
  x=>x.report.source_shape_measurements[0].registered_original_contact_x2_y2=[69,76]
 ]){const f=roots();alteration(f);await assert.rejects(check(f));}
});
