// Optional authenticated original source timeline, independent of all 2026 GLB poses.
// Original ROM phase/orientation integers are not calibrated physical joint angles.
export const SCHEMA = 'UR-ART4K-ORIGINAL-MESEN24-VIEWER-REFERENCE/1';
const ROM_SHA = '859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478';
const PPU_SHA = '28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6';
const POSE_SHA = '6286aedcda6080acf832ecece9fcdb879354db008e870bc00ada02db3ff3aa20';
const HEX64 = /^[a-f0-9]{64}$/;
const TICKS = Array.from({length:24},(_,i)=>1601+i);

export function validateOriginalMesen24(packet){
 if(!packet||packet.schema!==SCHEMA||packet.source_USA_ROM_sha256!==ROM_SHA||
   packet.original_Mesen24_source_sha256!==PPU_SHA||
   packet.exact_original_ROM_pose_receipt_sha256!==POSE_SHA||
   packet.original_1994_3D_mesh_camera_pose_recovered!==false||
   packet.original_source_to_2026_GLB_joint_pose_verified!==false||
   packet.source_sprite_index_zero_transparent!==true||
   JSON.stringify(packet.source_pixel_size)!=='[64,64]'||
   JSON.stringify(packet.display_pixel_aspect)!=='[7,6]'||
   !Array.isArray(packet.frames)||packet.frames.length!==48)
  throw Error('original 24-tick source manifest identity invalid');
 const seen=new Set();
 for(const row of packet.frames){
  const role=row?.role;
  if(!['blue','red'].includes(role)||!Number.isInteger(row.tick)||
    !TICKS.includes(row.tick)||!Number.isInteger(row.original_ROM_frame_ID)||
    row.original_ROM_frame_ID<0||row.original_ROM_frame_ID>=1536||
    row.source_phase_index!==Math.floor(row.original_ROM_frame_ID/64)||
    row.source_orientation_index!==row.original_ROM_frame_ID%64||
    row.original_OAM_slot!==(role==='blue'?96:97)||
    row.png!==role+'-'+row.tick+'.png'||
    !HEX64.test(row.png_sha256||'')||
    !HEX64.test(row.source_4bpp_plane_sha256||'')||
    !HEX64.test(row.source_RGBA_sha256||''))
   throw Error('original 24-tick source frame invalid');
  const id=role+':'+row.tick;
  if(seen.has(id))throw Error('duplicate original source tick');
  seen.add(id);
 }
 if(seen.size!==48||['blue','red'].some(role=>TICKS.some(t=>!seen.has(role+':'+t))))
  throw Error('incomplete original source chronology');
 return packet;
}

async function sourceSha256(bytes){
 if(!globalThis.crypto?.subtle)throw Error('secure-context SHA-256 unavailable');
 const digest=await globalThis.crypto.subtle.digest('SHA-256',bytes);
 return Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
}

export async function mountOriginalMesen24Rail(host){
 if(!host)return;
 host.replaceChildren();
 const title=document.createElement('h2');title.textContent='Executed original 24-tick source';
 const status=document.createElement('div');status.className='tiny';status.setAttribute('role','status');
 status.textContent='Checking original source sprite evidence…';
 const controls=document.createElement('div');controls.className='formrow';
 const player=document.createElement('select');player.setAttribute('aria-label','Original Mesen racer');player.disabled=true;
 for(const name of ['blue','red']){
  const opt=document.createElement('option');opt.value=name;opt.textContent=name==='blue'?'Original blue OAM96':'Original red OAM97';player.append(opt);
 }
 const tick=document.createElement('input');tick.type='range';tick.min='1601';tick.max='1624';tick.step='1';
 tick.value='1601';tick.setAttribute('aria-label','Original executed Mesen tick');tick.disabled=true;
 tick.style.width='100%';tick.style.minHeight='44px';
 controls.append(player,tick);
 const image=document.createElement('img');image.width=224;image.height=192;
 image.alt='Authentic source sprite unavailable';image.style.cssText='width:224px;height:192px;object-fit:contain;image-rendering:pixelated';
 const note=document.createElement('div');note.className='tiny';
 note.textContent='Original ROM state integers only. Source selection never changes the experimental GLB, camera or material.';
 host.append(title,controls,image,status,note);
 let packet=null,serial=0,objectURL=null;
 const loadFrame=async()=>{
  const request=++serial;
  if(!packet)return;
  const row=packet.frames.find(r=>r.role===player.value&&r.tick===Number(tick.value));
  if(!row){status.textContent='Original source frame unavailable';return;}
  status.textContent='Authenticating original ROM frame '+row.original_ROM_frame_ID+'…';
  try{
   const response=await fetch('./original-mesen24/'+row.png,{cache:'no-store'});
   if(!response.ok)throw Error('image HTTP '+response.status);
   const bytes=await response.arrayBuffer();
   if(await sourceSha256(bytes)!==row.png_sha256)throw Error('original PNG digest mismatch');
   if(request!==serial)return;
   const next=URL.createObjectURL(new Blob([bytes],{type:'image/png'}));
   const old=objectURL;objectURL=next;image.src=next;
   if(old)URL.revokeObjectURL(old);
   image.alt='Original '+row.role+' 64×64 source sprite, executed tick '+row.tick;
   status.textContent='Original tick '+row.tick+' · frame '+row.original_ROM_frame_ID+
     ' · phase '+row.source_phase_index+'/23 · orientation '+row.source_orientation_index+'/63'+
     ' · original 4bpp verified. No 3D pose or physical degree mapping.';
  }catch(e){
   if(request!==serial)return;
   image.removeAttribute('src');
   status.textContent='Original sprite withheld: '+e.message;
  }
 };
 player.onchange=loadFrame;
 tick.oninput=loadFrame;
 try{
  const response=await fetch('./original-mesen24/source-poses.json',{cache:'no-store'});
  if(!response.ok)throw Error('reference not published (HTTP '+response.status+')');
  packet=validateOriginalMesen24(await response.json());
  player.disabled=false;tick.disabled=false;
  await loadFrame();
 }catch(e){status.textContent='Optional original 24-tick rail unavailable: '+e.message;}
}
