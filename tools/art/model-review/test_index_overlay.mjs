import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {validateIndexLookup,originalIndexPlane,sourceIndexHighlight} from './index_overlay.mjs';
const digest=async bytes=>Array.from(new Uint8Array(await webcrypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');
const pixels=new Uint8ClampedArray(64*64*4);
pixels.set([42,21,9,0],4);pixels.set([240,30,30,255],8);pixels.set([40,70,220,255],12);
const source={width:64,height:64,data:pixels};
const expected=new Uint8Array(4096);expected[2]=3;expected[3]=7;
test('original ROM palette indices invert pixels and preserve transparent zero',async()=>{
 const record={source_binary_mask_sha256:await digest(new Uint8Array(4096)),original_4bpp_index_plane_sha256:await digest(expected),palette_rgb_to_index:{f01e1e:3,"2846dc":7}};
 const plane=await originalIndexPlane(source,record,webcrypto.subtle);
 assert.deepEqual(plane,expected);
 const result=sourceIndexHighlight(source,plane,7);
 assert.equal(result.count,1);
 assert.deepEqual(Array.from(result.data.slice(12,16)),[255,230,45,255]);
 assert.deepEqual(Array.from(source.data.slice(12,16)),[40,70,220,255]);
 await assert.rejects(originalIndexPlane(source,{...record,original_4bpp_index_plane_sha256:'0'.repeat(64)},webcrypto.subtle),/SHA mismatch/);
});
test('malformed source palettes and nonbinary alpha fail closed',async()=>{
 const record={source_binary_mask_sha256:'0'.repeat(64),original_4bpp_index_plane_sha256:await digest(expected),palette_rgb_to_index:{f01e1e:3,"2846dc":3}};
 await assert.rejects(originalIndexPlane(source,record,webcrypto.subtle),/Ambiguous/);
 const mixed={...source,data:new Uint8ClampedArray(source.data)};mixed.data[11]=128;
 await assert.rejects(originalIndexPlane(mixed,{...record,palette_rgb_to_index:{f01e1e:3,"2846dc":7}},webcrypto.subtle),/Non-binary/);
});
test('lookup authority refuses invented approvals and incomplete corpus',()=>{
 assert.throws(()=>validateIndexLookup({}),/Unrecognized/);
 assert.throws(()=>sourceIndexHighlight(source,expected,0),/Invalid/);
});
