// Authentic original 4bpp index inspection; independent of the 2026 GLB.
export const LOOKUP_SCHEMA='UR-ART4K-SOURCE-RGBA-TO-4BPP-INDEX-LOOKUP/1';
const SHA=/^[0-9a-f]{64}$/;
export function validateIndexLookup(packet){
 if(packet?.schema!==LOOKUP_SCHEMA||packet.source_images_verified!==41||
    packet.unique_index_planes_verified!==35||packet.original_3d_part_identity_verified!==false||
    packet.original_live_ppu_timing_verified!==false||packet.owner_likeness_approved!==false||
    !SHA.test(packet.authenticated_full_index_report_sha256)||
    !packet.rgba_to_index||Object.keys(packet.rgba_to_index).length!==41)
    throw Error('Unrecognized original index evidence');
 return packet;
}
export async function originalIndexPlane(imageData,record,subtle=globalThis.crypto?.subtle){
 if(imageData?.width!==64||imageData?.height!==64||imageData.data?.length!==64*64*4||
   !record||!SHA.test(record.original_4bpp_index_plane_sha256)||!SHA.test(record.source_binary_mask_sha256)||
   !record.palette_rgb_to_index||!subtle)throw Error('Missing authenticated source-index evidence');
 const palette=record.palette_rgb_to_index,plane=new Uint8Array(4096);
 const seen=new Set();
 for(const [rgb,index] of Object.entries(palette)){
  if(!/^[0-9a-f]{6}$/.test(rgb)||!Number.isInteger(index)||index<1||index>15||seen.has(index))
    throw Error('Ambiguous original opaque palette');
  seen.add(index);
 }
 for(let i=0;i<4096;i++){
  const j=4*i,a=imageData.data[j+3];
  if(a===0)continue;
  if(a!==255)throw Error('Non-binary original alpha');
  const rgb=[0,1,2].map(k=>imageData.data[j+k].toString(16).padStart(2,'0')).join('');
  const index=palette[rgb];
  if(!Number.isInteger(index))throw Error('Unmapped opaque source colour');
  plane[i]=index;
 }
 const hash=Array.from(new Uint8Array(await subtle.digest('SHA-256',plane)),n=>n.toString(16).padStart(2,'0')).join('');
 if(hash!==record.original_4bpp_index_plane_sha256)throw Error('Original 4bpp index SHA mismatch');
 return plane;
}
export function sourceIndexHighlight(imageData,plane,selected){
 if(imageData?.width!==64||imageData?.height!==64||plane?.length!==4096||
    !Number.isInteger(selected)||selected<1||selected>15)throw Error('Invalid palette index selection');
 const out=new Uint8ClampedArray(imageData.data),selectedCount=plane.reduce((n,v)=>n+(v===selected),0);
 for(let i=0;i<4096;i++){
  const j=i*4;
  if(plane[i]===selected){out[j]=255;out[j+1]=230;out[j+2]=45;out[j+3]=255;}
  else if(out[j+3]){out[j]=Math.floor(out[j]/3);out[j+1]=Math.floor(out[j+1]/3);out[j+2]=Math.floor(out[j+2]/3);}
 }
 return {data:out,count:selectedCount};
}
