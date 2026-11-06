#!/usr/bin/env node
// Browser acceptance: 1994 sprite rail + actual WebGL pose GLB, mobile and desktop.
// Uses Chrome DevTools directly. No npm dependencies or source ROM are needed.
import {createServer} from 'node:http';
import {spawn} from 'node:child_process';
import {readFileSync,existsSync,mkdirSync,writeFileSync,mkdtempSync,rmSync} from 'node:fs';
import {resolve,join,sep} from 'node:path';
import {tmpdir} from 'node:os';
import {SOURCE_SHA,sourcePhaseDelta} from './direct_drive_hypothesis.mjs';

const site=resolve(process.argv[2]||'.'), out=resolve(process.argv[3]||'.');
if(!existsSync(join(site,'model-review','sprites.json')))throw Error('Assemble atlas first');
mkdirSync(out,{recursive:true});
const pad=b=>Buffer.concat([b,Buffer.alloc((4-b.length%4)%4,0x20)]);
const positions=Buffer.alloc(36);
[-1,0,0,0,1,0,1,0,0].forEach((v,i)=>positions.writeFloatLE(v,i*4));
const indices=Buffer.alloc(8);[0,1,2].forEach((v,i)=>indices.writeUInt16LE(v,i*2));
const json=pad(Buffer.from(JSON.stringify({
  asset:{version:'2.0'},scenes:[{nodes:[0]}],scene:0,
  nodes:[{name:'tire',mesh:0}],meshes:[{primitives:[{attributes:{POSITION:0},indices:1}]}],
  buffers:[{byteLength:44}],
  bufferViews:[{buffer:0,byteOffset:0,byteLength:36,target:34962},
               {buffer:0,byteOffset:36,byteLength:6,target:34963}],
  accessors:[{bufferView:0,componentType:5126,count:3,type:'VEC3',min:[-1,0,0],max:[1,1,0]},
             {bufferView:1,componentType:5123,count:3,type:'SCALAR'}]
})));
const chunk=(content,type)=>{const header=Buffer.alloc(8);header.writeUInt32LE(content.length,0);header.write(type,4);return Buffer.concat([header,content])};
const a=chunk(json,'JSON'),b=chunk(Buffer.concat([positions,indices]),'BIN\0');
const header=Buffer.alloc(12);header.write('glTF');header.writeUInt32LE(2,4);header.writeUInt32LE(12+a.length+b.length,8);
const fakeGlb=Buffer.concat([header,a,b]);
let mocked=process.env.UR_MODEL_SMOKE_REAL!=='1';
const original=JSON.parse(readFileSync(join(site,'model-review/manifest.json'),'utf8'));
const modelManifest={...original,version:'SYNTHETIC BROWSER FIXTURE',model_url:'mock.glb',
  poses:Object.fromEntries(['upright','pedal','wheelie','stunt','bank'].map(p=>[p,{url:'mock.glb'}])),
  likeness_approved:false};
const mime={html:'text/html; charset=utf-8',js:'application/javascript; charset=utf-8',mjs:'application/javascript; charset=utf-8',css:'text/css; charset=utf-8',json:'application/json; charset=utf-8',png:'image/png',glb:'model/gltf-binary',svg:'image/svg+xml'};
const server=createServer((req,res)=>{
  let path;
  try{path=decodeURIComponent((req.url||'/').split('?')[0])}catch{res.writeHead(400);res.end();return}
  if(mocked&&path==='/model-review/manifest.json'){
    res.writeHead(200,{'Content-Type':mime.json,'Cache-Control':'no-store'});res.end(JSON.stringify(modelManifest));return}
  if(path==='/model-review/mock.glb'){
    res.writeHead(200,{'Content-Type':mime.glb});res.end(fakeGlb);return}
  const file=resolve(site,'.'+(path.endsWith('/')?path+'index.html':path));
  if(!file.startsWith(site+sep)){res.writeHead(403);res.end();return}
  let payload;
  try{payload=readFileSync(file)}catch{res.writeHead(404);res.end('missing');return}
  res.writeHead(200,{'Content-Type':mime[file.split('.').at(-1)]||'application/octet-stream','Cache-Control':'no-store'});
  res.end(payload)
});
await new Promise(done=>server.listen(0,'127.0.0.1',done));
const address='http://127.0.0.1:'+server.address().port+'/model-review/';
const chromeDir=mkdtempSync(join(tmpdir(),'ur-model-chromium-'));
const portServer=createServer();await new Promise(done=>portServer.listen(0,'127.0.0.1',done));const port=portServer.address().port;await new Promise(done=>portServer.close(done));
let chromeError='';
const chrome=spawn(process.env.CHROME_BIN||'/usr/bin/google-chrome',[
 '--headless=new','--no-sandbox','--disable-dev-shm-usage','--no-first-run',
 '--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader',
 '--remote-debugging-port='+port,'--user-data-dir='+chromeDir,'about:blank'
],{stdio:['ignore','ignore','pipe']});
chrome.stderr.on('data',d=>chromeError=(chromeError+String(d)).slice(-2000));
const sleep=ms=>new Promise(done=>setTimeout(done,ms));
let ws,session,id=0;
const pending=new Map();
function cdp(method,params={},sessionId){
 return new Promise((resolve,reject)=>{
  const n=++id,timeout=setTimeout(()=>{pending.delete(n);reject(Error('CDP timeout: '+method))},15000);
  pending.set(n,{resolve:value=>{clearTimeout(timeout);resolve(value)},reject:e=>{clearTimeout(timeout);reject(e)}});
  ws.send(JSON.stringify({id:n,method,params,...(sessionId?{sessionId}:{})}));
 });
}
async function evaluate(expression){
 const data=await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},session);
 if(data.exceptionDetails)throw Error('Chromium evaluation: '+JSON.stringify(data.exceptionDetails).slice(0,500));
 return data.result?.value;
}
try{
 let endpoint;
 for(let i=0;i<200;i++){
  try{const r=await fetch('http://127.0.0.1:'+port+'/json/version');if(r.ok){endpoint=(await r.json()).webSocketDebuggerUrl;if(endpoint)break}}catch{}
  if(chrome.exitCode!==null)break;await sleep(100);
 }
 if(!endpoint)throw Error('Chrome did not start: '+chromeError);
 ws=new WebSocket(endpoint);
 await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true})});
 ws.addEventListener('message',e=>{let x;try{x=JSON.parse(e.data)}catch{return}const p=pending.get(x.id);if(!p)return;pending.delete(x.id);if(x.error)p.reject(Error(x.error.message));else p.resolve(x.result||{})});
 const target=await cdp('Target.createTarget',{url:'about:blank'});
 session=(await cdp('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;
 await cdp('Page.enable',{},session);await cdp('Runtime.enable',{},session);
 const summaries=[];
 for(const [width,height] of [[320,700],[412,892],[1440,900]]){
  await cdp('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<600},session);
  await cdp('Page.navigate',{url:address+(mocked?'':'?art4k-still=1')},session);
  let ready=false;
  for(let i=0;i<150;i++){
   ready=await evaluate("document.getElementById('source')?.textContent.includes('published current model') && document.getElementById('sprite')?.naturalWidth===64");
   if(ready)break;await sleep(100);
  }
  if(!ready)throw Error('Model/sprite did not load at '+width+'px; state '+await evaluate("document.getElementById('state')?.textContent"));
  const report=await evaluate(`(async function(){
   const issues=[],q=id=>document.getElementById(id),w=innerWidth;
   if(document.documentElement.scrollWidth>w+1)issues.push('horizontal overflow');
   const panel=document.querySelector('.panel');
   if(panel&&panel.scrollWidth>panel.clientWidth+1)
     issues.push('model-review panel horizontal overflow');
   if(!document.querySelector('#viewport canvas'))issues.push('no WebGL canvas');
   if(!q('parts').textContent.includes('tire'))issues.push('no glTF part');
   if(!q('sourceInfo').textContent.includes('frame 1205'))issues.push('missing original provenance');
   const manualLink=q('manualFigureLink');
   if(!manualLink||manualLink.getAttribute('href')!=='./manual-landmarks.html')
    issues.push('no local source printed-manual annotator link');
   else{
    if(manualLink.getBoundingClientRect().height<12)
      issues.push('original manual annotator link hidden');
    const downloaded=await fetch(manualLink.href);
    const page=downloaded.ok?await downloaded.text():'';
    if(!downloaded.ok||!page.includes('manual_landmark_marking.mjs')||
       !page.includes('No images are uploaded')||
       !page.includes('id="partialSurface"')||!page.includes('id="surfaceStart"')||
       !page.includes('id="surfaceFinish"'))
      issues.push('local manual PNG annotation page not published');
    const pureHelper=await fetch('./manual_landmark_marking.mjs');
    if(!pureHelper.ok||!((await pureHelper.text()).includes('source_pdf_sha256')))
      issues.push('mobile manual source annotation helper not published');
   }
   const sourceBeforePrintViews=q('sourceInfo').textContent;
   for(const [label,page] of [['Print fork','14'],['Print hub','15']]){
    const choice=[...q('views').querySelectorAll('button')].find(b=>b.textContent===label);
    if(!choice){issues.push('missing manual-inspired 3D '+label);continue}
    if(choice.getBoundingClientRect().height<44)issues.push('manual camera touch target');
    choice.click();
    const status=q('manualViewStatus');
    if(status?.dataset.preset!==(label==='Print fork'?'print-fork':'print-hub')||
       !status.textContent.includes('p.'+page)||
       !status.textContent.includes('source camera is uncalibrated'))
      issues.push('manual 3D camera provenance/feedback unavailable '+label);
    if(q('sourceInfo').textContent!==sourceBeforePrintViews)
      issues.push('manual camera changed original reference image identity');
   }
   q('reset').click();
   // Independent authenticated 24-tick original-ROM states must not alter
   // the preexisting source sprite, selected GLB or scene pose.
   const originalRail=q('originalMesen24Rail');
   if(!originalRail)issues.push('original Mesen24 rail missing');
   else{
     const sourceSelect=originalRail.querySelector('select');
     const sourceTick=originalRail.querySelector('input[type=range]');
     const sourceImg=originalRail.querySelector('img');
     for(let i=0;i<80&&(!originalRail.textContent.includes('Original tick 1601')||sourceImg?.naturalWidth!==64);i++)
       await new Promise(done=>setTimeout(done,50));
     if(!sourceSelect||!sourceTick||!sourceImg||
        !originalRail.textContent.includes('Original tick 1601')||
        sourceImg.naturalWidth!==64)issues.push('source authentic tick1601 load');
     else{
       const beforeGLB=q('source').textContent, beforeStock=q('sourceInfo').textContent;
       sourceSelect.value='red';sourceSelect.dispatchEvent(new Event('change'));
       sourceTick.value='1603';sourceTick.dispatchEvent(new Event('input'));
       for(let i=0;i<80&&!originalRail.textContent.includes('Original tick 1603');i++)
         await new Promise(done=>setTimeout(done,50));
       if(!originalRail.textContent.includes('Original tick 1603')||
          !originalRail.textContent.includes('phase 1/23')||
          !originalRail.textContent.includes('orientation 57/63'))
         issues.push('red source ROM frame ID/phase/orientation selection');
       if(sourceSelect.getBoundingClientRect().height<44||
          sourceTick.getBoundingClientRect().height<44)
         issues.push('original Mesen source touch targets');
       if(q('source').textContent!==beforeGLB||q('sourceInfo').textContent!==beforeStock)
         issues.push('original source selector mutated GLB or stock sprite');
     }
   }
   q('frame').value='1210';q('frame').dispatchEvent(new Event('input'));
   if(!q('sourceInfo').textContent.includes('frame 1210'))issues.push('sprite scrub');
   if(!q('spriteIndex')||q('spriteIndex').disabled)issues.push('index selector unavailable');
   else{
     q('spriteIndex').value='7';q('spriteIndex').dispatchEvent(new Event('change'));
     for(let i=0;i<80&&!q('indexStatus').textContent.includes('Index 7:');i++)
       await new Promise(done=>setTimeout(done,50));
     if(!q('indexStatus').textContent.includes('Index 7:')||
        q('indexCanvas').hidden||!q('sprite').hidden)issues.push('authenticated original index isolate');
     q('spriteIndex').value='original';q('spriteIndex').dispatchEvent(new Event('change'));
     if(!q('indexCanvas').hidden||q('sprite').hidden)issues.push('original sprite restoration');
   }
   q('pose-bank').click();
   for(let i=0;i<100 && !q('source').textContent.includes('published bank GLB');i++)await new Promise(done=>setTimeout(done,50));
   if(!q('source').textContent.includes('published bank GLB'))issues.push('pose switch');
   if(q('wheelWide').getBoundingClientRect().height<44||q('wheelOriginal').getBoundingClientRect().height<44)
     issues.push('wheel hypothesis touch target');
   if(${mocked}) {
     if(!q('wheelWide').disabled)issues.push('synthetic GLB falsely enabled width experiment');
   } else {
     if(q('wheelWide').disabled)issues.push('real seven-mesh wheel hypothesis unavailable');
     else {
       const originalNames=q('parts').textContent;
       q('wheelWide').click();
       if(q('wheelWide').getAttribute('aria-pressed')!=='true' ||
          !q('wheelHypothesisStatus').textContent.includes('10%'))issues.push('wider wheel toggle');
       q('wheelOriginal').click();
       if(q('wheelOriginal').getAttribute('aria-pressed')!=='true' ||
          !q('wheelHypothesisStatus').textContent.includes('Unmodified'))issues.push('wheel reset');
       if(q('parts').textContent!==originalNames)issues.push('wheel toggle mutated part names');
     }
   }
   if(q('frameHinge').getBoundingClientRect().height<44)
     issues.push('frame hinge touch target');
   if(${mocked}){
     if(!q('frameHinge').disabled)
       issues.push('synthetic tire-only GLB falsely enabled axle hinge');
   } else {
     if(q('frameHinge').disabled)issues.push('real five-parent frame hinge unavailable');
     else {
       const originalIdentity=q('source').textContent;
       const attr=()=>Object.fromEntries(['tireMatrix','rimMatrix','pedalsMatrix','forkMatrix','saddleMatrix']
                        .map(name=>[name,q('frameHingeStatus').dataset[name]||'']));
       const initial=attr();
       if(Object.values(initial).some(value=>!value))issues.push('source part transforms not available');
       let last=initial;
       for(const [value,label] of [['-40','-40'],['20','20'],['0','Unmodified']]){
         q('frameHinge').value=value;
         q('frameHinge').dispatchEvent(new Event('change',{bubbles:true}));
         if(q('frameHinge').value!==value || !q('frameHingeStatus').textContent.includes(label))
           issues.push('frame hinge selection '+value);
         const now=attr();
         for(const key of ['tireMatrix','rimMatrix','pedalsMatrix']){
           if(now[key]!==initial[key])issues.push('frame hinge altered stationary '+key+' at '+value);
         }
         if(value!=='0'){
           for(const key of ['forkMatrix','saddleMatrix']){
             if(now[key]===initial[key]||now[key]===last[key])
               issues.push('frame hinge failed to move '+key+' at '+value);
           }
         }else if(Object.keys(initial).some(key=>now[key]!==initial[key])){
           issues.push('frame hinge 0 degree reset mutated original source transforms');
         }
         last=now;
       }
       if(q('source').textContent!==originalIdentity)
         issues.push('frame hinge changed actual GLB source identity');
       if(!q('frameHingeStatus').textContent.includes('Unmodified'))
         issues.push('frame hinge failed to reset original pose');
     }
   }
   if(q('wheelDrive').getBoundingClientRect().height<44)
     issues.push('source direct drive touch target');
   if(${mocked}){
     if(!q('wheelDrive').disabled)
       issues.push('synthetic non-source GLB falsely enabled direct drive');
   }else{
     if(q('wheelDrive').disabled)issues.push('real source-owned wheel drive unavailable');
     else{
       const originalSource=q('source').textContent;
       const get=()=>Object.fromEntries(['tireMatrix','rimMatrix','pedalsMatrix','forkMatrix','saddleMatrix']
         .map(k=>[k,q('wheelDriveStatus').dataset[k]||'']));
       const before=get();
       q('wheelDrive').value='1';q('wheelDrive').dispatchEvent(new Event('change',{bubbles:true}));
       const spinning=get();
       for(const k of ['tireMatrix','rimMatrix']){
         if(spinning[k]===before[k])issues.push('direct drive failed to rotate '+k);
       }
       for(const k of ['pedalsMatrix','forkMatrix','saddleMatrix']){
         if(spinning[k]!==before[k])issues.push('direct drive moved stationary '+k);
       }
       q('wheelDrive').value='0';q('wheelDrive').dispatchEvent(new Event('change',{bubbles:true}));
       if(Object.keys(before).some(k=>get()[k]!==before[k]))
         issues.push('direct drive source matrices not restored');
       // Test both independent axle-centred controls together, then exact resets.
       const forkAtZero=q('frameHingeStatus').dataset.forkMatrix;
       q('frameHinge').value='-40';q('frameHinge').dispatchEvent(new Event('change',{bubbles:true}));
       const forkLeaning=q('frameHingeStatus').dataset.forkMatrix;
       if(forkLeaning===forkAtZero)issues.push('frame hinge failed before combined axle test');
       q('wheelDrive').value='1';q('wheelDrive').dispatchEvent(new Event('change',{bubbles:true}));
       const combined=get();
       if(combined.rimMatrix===before.rimMatrix || combined.tireMatrix===before.tireMatrix)
         issues.push('drive phase cannot coexist with leaning frame');
       if(q('frameHingeStatus').dataset.forkMatrix!==forkLeaning)
         issues.push('wheel sync altered independent fork hinge');
       q('wheelDrive').value='0';q('wheelDrive').dispatchEvent(new Event('change',{bubbles:true}));
       if(get().rimMatrix!==before.rimMatrix || get().tireMatrix!==before.tireMatrix)
         issues.push('combined drive reset did not restore wheel');
       q('frameHinge').value='0';q('frameHinge').dispatchEvent(new Event('change',{bubbles:true}));
       if(q('frameHingeStatus').dataset.forkMatrix!==forkAtZero)
         issues.push('combined hinge reset did not restore frame');
       if(q('source').textContent!==originalSource)
         issues.push('direct drive source GLB identity changed');
     }
   }
   // Guard against the 45-degree symmetry alias and cumulative drift.
   if(q('crankScrub').getBoundingClientRect().height<44)
     issues.push('continuous crank slider touch target');
   if(${mocked}){
     if(!q('crankScrub').disabled)
       issues.push('synthetic non-source GLB falsely enabled crank scrub');
   }else{
     if(q('crankScrub').disabled)issues.push('real source-owned crank scrub disabled');
     else{
       const sourceLabel=q('source').textContent;
       // Refresh the ledger after prior independent fork/saddle hinge tests.
       q('wheelDrive').value='0';
       q('wheelDrive').dispatchEvent(new Event('change',{bubbles:true}));
       const get=()=>Object.fromEntries(['tireMatrix','rimMatrix','pedalsMatrix','forkMatrix','saddleMatrix']
          .map(k=>[k,q('wheelDriveStatus').dataset[k]||'']));
       const original=get();
       function scrub(i){
         q('crankScrub').value=String(i);
         q('crankScrub').dispatchEvent(new Event('input',{bubbles:true}));
         if(q('crankScrub').value!==String(i)||
            !q('crankStatus').textContent.includes(i+'/64'))
           issues.push('continuous crank step update '+i);
         return get();
       }
       const one=scrub(1),two=scrub(2),three=scrub(3),four=scrub(4);
       for(const k of ['tireMatrix','rimMatrix','pedalsMatrix']){
         if(one[k]===original[k]||one[k]===two[k]||two[k]===three[k]||three[k]===four[k])
           issues.push('continuous crank failed to advance '+k);
       }
       for(const k of ['forkMatrix','saddleMatrix']){
         if([one,two,three,four].some(v=>v[k]!==original[k]))
           issues.push('continuous crank moved independent '+k);
       }
       const end=scrub(64);
       if(end.pedalsMatrix!==original.pedalsMatrix)
         issues.push('720-degree crank did not return pedals exactly');
       const reset=scrub(0);
       if(Object.keys(original).some(k=>reset[k]!==original[k]))
         issues.push('continuous crank zero did not restore original TRS');
       if(q('wheelDrive').value!=='0')
         issues.push('continuous crank original wheel-sync preference lost');
       q('wheelDrive').value='1';q('wheelDrive').dispatchEvent(new Event('change',{bubbles:true}));
       const enabled=get();
       scrub(2);const back=scrub(0);
       if(Object.keys(enabled).some(k=>back[k]!==enabled[k]))
         issues.push('drive-enabled crank scrub zero changed original matrices');
       if(q('wheelDrive').value!=='1')
         issues.push('drive-enabled preference lost after crank scrub');
       q('wheelDrive').value='0';q('wheelDrive').dispatchEvent(new Event('change',{bubbles:true}));
       if(Object.keys(original).some(k=>get()[k]!==original[k]))
         issues.push('continuous crank final original state mismatch');
       if(q('source').textContent!==sourceLabel)
         issues.push('continuous crank changed original GLB identity');
       // A new published GLB must never inherit an old pose's crank state.
       scrub(3);
       q('pose-pedal').click();
       for(let attempt=0;attempt<160 && !q('source').textContent.includes('published pedal GLB');attempt++)
         await new Promise(done=>setTimeout(done,25));
       if(!q('source').textContent.includes('published pedal GLB') ||
          q('crankScrub').value!=='0' || q('wheelDrive').value!=='0')
         issues.push('continuous crank not reset on named pose change');
       q('pose-bank').click();
       for(let attempt=0;attempt<160 && !q('source').textContent.includes('published bank GLB');attempt++)
         await new Promise(done=>setTimeout(done,25));
       if(!q('source').textContent.includes('published bank GLB') ||
          q('crankScrub').value!=='0')
         issues.push('continuous crank leaked across published pose return');
     }
   }
   if(q('upperShape').getBoundingClientRect().height<44)
     issues.push('upper 2026 geometry preview touch target too small');
   // The 1994 source rail must never automatically drive 2026 shapes.
   if(${mocked}){
     if(!q('upperShape').disabled)
       issues.push('untrusted synthetic model enabled authored upper geometry');
   }else{
     if(q('frameHinge').value!=='0'){
       q('frameHinge').value='0';
       q('frameHinge').dispatchEvent(new Event('change',{bubbles:true}));
     }
     if(q('upperShape').disabled)issues.push('published real model upper-shape control unavailable');
     else{
       const status=q('upperShapeStatus'),initial=status.dataset.saddlePosition;
       function upperPreview(mode){
         q('upperShape').value=mode;
         q('upperShape').dispatchEvent(new Event('change',{bubbles:true}));
         if(q('upperShape').value!==mode||status.dataset.mode!==mode||
            status.textContent.includes('unavailable:'))
           issues.push('real 2026 upper-shape preview failed '+mode);
         return status.dataset.saddlePosition;
       }
       const up=upperPreview('saddle-up');
       const down=upperPreview('saddle-down');
       if(up===initial||down===initial||up===down)
         issues.push('saddle preview failed to move actual source parent');
       const short=upperPreview('frame-short');
       const long=upperPreview('frame-long');
       if(short===long||short===initial||long===initial)
         issues.push('frame stretch failed to translate actual 2026 saddle mount');
       const narrow=upperPreview('saddle-narrow');
       if(status.dataset.saddleSpan!=='0.90'||narrow!==initial)
         issues.push('real saddle contour 0.90 shape changed original mount');
       const wide=upperPreview('saddle-wide');
       if(status.dataset.saddleSpan!=='1.10'||wide!==initial)
         issues.push('real saddle contour 1.10 shape changed original mount');
       const deepCup=upperPreview('saddle-cup-deep');
       if(status.dataset.saddleCup!=='-0.08'||deepCup!==initial)
         issues.push('source GLB saddle center hollow depth moved original mount');
       const softCup=upperPreview('saddle-cup-soft');
       if(status.dataset.saddleCup!=='0.08'||softCup!==initial)
         issues.push('source GLB saddle center hollow softness moved original mount');
       const narrowCrown=upperPreview('fork-crown-narrow');
       if(status.dataset.crownScale!=='0.90'||narrowCrown!==initial)
         issues.push('source GLB fork crown narrow moved original saddle mount');
       const fullCrown=upperPreview('fork-crown-full');
       if(status.dataset.crownScale!=='1.10'||fullCrown!==initial)
         issues.push('source GLB fork crown fuller moved original saddle mount');
       upperPreview('original');
       if(status.dataset.saddlePosition!==initial||status.dataset.saddleSpan!=='1.00'||
          status.dataset.saddleCup!=='0.00'||status.dataset.crownScale!=='1.00')
         issues.push('upper-shape preview failed to restore saddle parent exactly');
       q('frameHinge').value='20';
       q('frameHinge').dispatchEvent(new Event('change',{bubbles:true}));
       if(!q('upperShape').disabled||q('upperShape').value!=='original')
         issues.push('experimental frame hinge wrongly combined with mesh stretch');
       q('frameHinge').value='0';
       q('frameHinge').dispatchEvent(new Event('change',{bubbles:true}));
       if(q('upperShape').disabled)issues.push('upper-shape preview did not re-enable');
     }
   }
   const blades=q('bladeSpokes');
   if(!blades||blades.getBoundingClientRect().height<44)
     issues.push('source-authored wheel blade preview mobile touch target');
   if(${mocked}){if(!blades?.disabled)
      issues.push('synthetic GLB enabled source blade sculpt');}
   else if(blades?.disabled)issues.push('real original-2026 source spoke volume control unavailable');
   else{
     const before=q('sourceInfo').textContent, parts=q('parts').textContent;
     blades.value='blade';blades.dispatchEvent(new Event('change',{bubbles:true}));
     if(q('bladeSpokesStatus').dataset.mode!=='blade'||
        q('bladeSpokesStatus').dataset.sourceVertices!=='1788')
       issues.push('2026 real source blade 1788-vertex volume preview failed');
     blades.value='original';blades.dispatchEvent(new Event('change',{bubbles:true}));
     if(q('bladeSpokesStatus').dataset.mode!=='original'||
        q('sourceInfo').textContent!==before||q('parts').textContent!==parts)
       issues.push('2026 source spoke preview mutated authentic 1994 rail or GLB materials');
   }
   const hub=q('hubFace');
   if(!hub||hub.getBoundingClientRect().height<44)
     issues.push('source 2026 dark hub touch target');
   if(${mocked}){
     if(!hub?.disabled)issues.push('synthetic GLB enabled dark hub cover');
   }else if(hub?.disabled)issues.push('exact-source dark hub cover disabled');
   else{
     const priorSource=q('sourceInfo').textContent;
     const priorParts=q('parts').textContent;
     const priorModel=q('source').textContent;
     hub.value='cover';hub.dispatchEvent(new Event('change',{bubbles:true}));
     if(q('hubFaceStatus').dataset.mode!=='cover'||
        q('hubFaceStatus').dataset.sourceVertices!=='100')
       issues.push('real 2026 hub cover geometry mode unavailable');
     hub.value='axle-locked';hub.dispatchEvent(new Event('change',{bubbles:true}));
     if(q('hubFaceStatus').dataset.mode!=='axle-locked'||
        q('hubFaceStatus').dataset.counterspinDegrees!=='0')
       issues.push('source axle-locked 2026 hub preview not available');
     hub.value='original';hub.dispatchEvent(new Event('change',{bubbles:true}));
     if(q('hubFaceStatus').dataset.mode!=='original'||
        q('sourceInfo').textContent!==priorSource||
        q('parts').textContent!==priorParts||q('source').textContent!==priorModel)
       issues.push('reversible dark hub cover altered original 1994 sprite or GLB part census');
   }
   if(q('paintHypothesis').getBoundingClientRect().height<44)
     issues.push('paint hypothesis touch target too small');
   if(q('modelColourway').getBoundingClientRect().height<44)
     issues.push('model colourway touch target too small');
   if(${mocked}){
     if(!q('paintHypothesis').disabled)
       issues.push('synthetic non-source model falsely enabled paint hypotheses');
     if(!q('modelColourway').disabled)
       issues.push('synthetic non-source model falsely enabled colourways');
   }else{
     if(q('paintHypothesis').disabled)issues.push('real source GLB paint hypothesis disabled');
     if(q('modelColourway').disabled)issues.push('real source GLB model colourway disabled');
     else{
       const old=q('source').textContent,partNames=q('parts').textContent;
       const paintBefore=q('paintStatus').dataset.materialState;
       q('modelColourway').value='p1';
       q('modelColourway').dispatchEvent(new Event('change',{bubbles:true}));
       if(q('modelColourway').value!=='p1'||
          q('modelColourwayStatus').dataset.modelColourState!=='p1:temporary-red'||
          q('modelColourwayStatus').textContent.includes('unavailable'))
         issues.push('model colourway not implemented');
       if(q('source').textContent!==old||q('parts').textContent!==partNames||
          q('paintStatus').dataset.materialState!==paintBefore)
         issues.push('model colourway changed GLB source identity');
       q('modelColourway').value='p2';
       q('modelColourway').dispatchEvent(new Event('change',{bubbles:true}));
       if(q('modelColourwayStatus').dataset.modelColourState!=='p2:source-original')
         issues.push('model colourway original not restored');
     }
     if(!q('paintHypothesis').disabled){
       const source=q('source').textContent,parts=q('parts').textContent;
       const original=q('paintStatus').dataset.materialState;
       if(!original||original.includes(':temporary'))
         issues.push('source blue material state not originally restored');
       function choosePaint(value,expected){
         q('paintHypothesis').value=value;
         q('paintHypothesis').dispatchEvent(new Event('change',{bubbles:true}));
         const actual=q('paintStatus').dataset.materialState||'';
         if(q('paintHypothesis').value!==value ||
            !q('paintStatus').textContent.includes(value==='original'?'Unmodified':'Temporary') ||
            actual.split(':temporary').length-1!==expected.length)
           issues.push('paint material choice not implemented '+value);
         for(const name of expected){
           if(!actual.includes(name+':temporary'))
             issues.push('paint material not recoloured '+name);
         }
         return actual;
       }
       choosePaint('area',['rim_and_hub__material_1','pedals__material_1']);
       choosePaint('disc',['rim_and_hub__material_2','pedals__material_1']);
       choosePaint('discPlus',['rim_and_hub__material_2','pedals__material_0','pedals__material_1']);
       // Regression: material replacement must preserve the active Wireframe
       // preference on ALL original and temporary 2026 material nodes.
       choosePaint('disc',['rim_and_hub__material_2','pedals__material_1']);
       q('wire').click();
       if(q('wire').getAttribute('aria-pressed')!=='true')
         issues.push('wireframe unavailable before paint mode transition');
       for(const choice of ['area','original','discPlus','original']){
         choosePaint(choice,choice==='area'?['rim_and_hub__material_1','pedals__material_1']:
           choice==='discPlus'?['rim_and_hub__material_2','pedals__material_0','pedals__material_1']:[]);
         if(q('paintStatus').dataset.materialWireframe?.split(':wire').length-1!==4)
           issues.push('paint transition lost active wireframe '+choice);
       }
       q('wire').click();
       if(q('wire').getAttribute('aria-pressed')!=='false'||
          q('paintStatus').dataset.materialWireframe?.includes(':wire'))
         issues.push('wireframe off did not restore solid material render');
       const restored=choosePaint('original',[]);
       if(restored!==original)
         issues.push('paint experiment failed exact original material restoration');
       if(q('source').textContent!==source||q('parts').textContent!==parts)
         issues.push('paint experiment changed source GLB identity or mesh census');
       choosePaint('disc',['rim_and_hub__material_2','pedals__material_1']);
       q('pose-pedal').click();
       for(let attempt=0;attempt<160&&!q('source').textContent.includes('published pedal GLB');attempt++)
         await new Promise(done=>setTimeout(done,25));
       if(q('paintHypothesis').value!=='original'||
          q('paintHypothesis').disabled ||
          q('paintStatus').dataset.materialState?.includes(':temporary'))
         issues.push('paint experiment persisted after changing actual published GLB');
       q('pose-bank').click();
       for(let attempt=0;attempt<160&&!q('source').textContent.includes('published bank GLB');attempt++)
         await new Promise(done=>setTimeout(done,25));
       if(!q('source').textContent.includes('published bank GLB')||
          q('paintHypothesis').value!=='original')
         issues.push('paint experiment leaked across named pose roundtrip');
       if(q('modelColourway').disabled||
          q('modelColourway').value!=='p2'||
          q('modelColourwayStatus').dataset.modelColourState!=='p2:source-original')
         issues.push('model colourway persisted across named pose');
     }
   }
   if(q('rootLean').getBoundingClientRect().height<44)
     issues.push('root lean accessible touch target');
   if(q('rootLean').disabled)issues.push('source GLB root lean selector unavailable');
   const sourceBeforeLean=q('source').textContent;
   const beforeTire=Number(q('rootLeanStatus').dataset.tireLowerY);
   const beforeRoot=Number(q('rootLeanStatus').dataset.rootY);
   function rootPose(value){
     q('rootLean').value=value;
     q('rootLean').dispatchEvent(new Event('change',{bubbles:true}));
   }
   function sameSourceLower(label,checkRoot){
     const tire=Number(q('rootLeanStatus').dataset.tireLowerY);
     const root=Number(q('rootLeanStatus').dataset.rootY);
     if(!Number.isFinite(tire)||!Number.isFinite(root)||
        Math.abs(tire-beforeTire)>1e-5||
        (checkRoot&&Math.abs(root-beforeRoot)>1e-5))
       issues.push('root pose visually changed original tire baseline '+label);
   }
   if(!q('rootLeanStatus').dataset.tireLowerY||
      !Number.isFinite(beforeTire)||!Number.isFinite(beforeRoot))
     issues.push('source tire baseline unavailable');
   for(const [value,expected] of [['-35','-35'],['15','15'],['0','Unchanged']]){
     rootPose(value);
     if(q('rootLean').value!==value || !q('rootLeanStatus').textContent.includes(expected))
       issues.push('source-root lean preset '+value);
     sameSourceLower('change '+value,value==='0');
   }
   rootPose('-35');q('reset').click();rootPose('0');
   sameSourceLower('camera-only reset under lean',true);
   rootPose('-35');q('zup').click();q('zup').click();rootPose('0');
   sameSourceLower('zup off/on under lean',true);
   if(q('source').textContent!==sourceBeforeLean)
     issues.push('root lean mutated original source identity');
   q('wire').click();if(q('wire').getAttribute('aria-pressed')!=='true')issues.push('wireframe');
   q('spin').click();if(q('spin').getAttribute('aria-pressed')!=='true')issues.push('orbit');
   q('zup').click();if(q('zup').checked)issues.push('up-axis');
   if(q('measureToggle').getBoundingClientRect().height<44)issues.push('research touch target');
   q('measureToggle').click();
   for(let i=0;i<100 && q('measureToggle').disabled;i++)await new Promise(done=>setTimeout(done,50));
   const research=q('measureStatus').textContent;
   if(${mocked}) {
    if(!research.includes('Research comparison unavailable')||!q('measurements').hidden)
     issues.push('missing sidecar did not fail closed');
   } else {
    if(!research.includes('Verified research packet')||q('measurements').hidden||
       q('measureResults').querySelectorAll('tbody tr').length!==5)
     issues.push('real source measurements unavailable');
    if(q('measureResults').textContent.includes('authentic original-game pose match'))
     issues.push('invented original sprite mapping');
   }
   if(!q('source').textContent.includes('published bank GLB'))issues.push('research changes displayed GLB');
   return {width:w,height:innerHeight,issues,research:research.slice(0,90),source:q('sourceInfo').textContent.slice(0,85)};
  })()`);
  // Explicit synchronous original/alternative/original GLB canvas rendering.
  // Query-gated test hook stops the OrbitControls animation loop, avoiding
  // camera damping, compositor timing and CDP screenshot aliasing entirely.
  if(!mocked && width===412){
   const frozen=await evaluate("(()=>{const q=id=>document.getElementById(id);if(q('spin').getAttribute('aria-pressed')==='true')q('spin').click();if(q('wire').getAttribute('aria-pressed')==='true')q('wire').click();if(!q('zup').checked)q('zup').click();q('reset').click();return q('spin').getAttribute('aria-pressed')==='false'&&q('wire').getAttribute('aria-pressed')==='false'&&q('zup').checked&&q('paintHypothesis').value==='original'&&!!window.__urArt4kVisualReadback})()");
   if(!frozen)throw Error('source GLB still-frame capture hook/camera unavailable');
   const capture=async()=> {
     const png=await evaluate("window.__urArt4kVisualReadback.snapshot()");
     if(!png?.startsWith('data:image/png;base64,'))throw Error('actual GLB canvas readback absent');
     return Buffer.from(png.slice('data:image/png;base64,'.length),'base64');
   };
   // First call consumes any residual OrbitControls damping. This exact camera
   // is subsequently frozen and reused across the THREE render calls below.
   await capture();
   const originalPaint=await capture();
   const changed=await evaluate("(()=>{const c=document.getElementById('paintHypothesis');if(c.disabled)return false;c.value='disc';c.dispatchEvent(new Event('change',{bubbles:true}));return c.value==='disc'})()");
   if(!changed)throw Error('real GLB paint preview not accessible');
   const alternativePaint=await capture();
   await evaluate("(()=>{const c=document.getElementById('paintHypothesis');c.value='original';c.dispatchEvent(new Event('change',{bubbles:true}))})()");
   const exactRestored=await capture();
   if(originalPaint.equals(alternativePaint))
     throw Error('actual 3D paint hypothesis changed labels but not GLB viewport pixels');
   if(!originalPaint.equals(exactRestored))
     throw Error('stationary original 3D GLB paint pixels not exactly restored');
   writeFileSync(join(out,'model-review-paint-original-412.png'),originalPaint);
   writeFileSync(join(out,'model-review-paint-disc-412.png'),alternativePaint);
   const redSet=await evaluate("(()=>{const c=document.getElementById('modelColourway');if(c.disabled)return false;c.value='p1';c.dispatchEvent(new Event('change',{bubbles:true}));return document.getElementById('modelColourwayStatus').dataset.modelColourState==='p1:temporary-red'})()");
   if(!redSet)throw Error('source-authenticated P1 red material preview unavailable');
   const redFrame=await capture();
   await evaluate("(()=>{const c=document.getElementById('modelColourway');c.value='p2';c.dispatchEvent(new Event('change',{bubbles:true}))})()");
   const restoredBlue=await capture();
   if(originalPaint.equals(redFrame))
     throw Error('provisional red change did not alter actual GLB viewport pixels');
   if(!originalPaint.equals(restoredBlue))
     throw Error('provisional red model pixels not exactly restored');
   writeFileSync(join(out,'model-review-p1-red-412.png'),redFrame);
   writeFileSync(join(out,'model-review-p2-blue-412.png'),restoredBlue);
   const setSaddle=async(mode)=>evaluate("(()=>{const q=document.getElementById('upperShape');if(q.disabled)return false;q.value='"+mode+"';q.dispatchEvent(new Event('change',{bubbles:true}));return q.value==='"+mode+"'&&document.getElementById('upperShapeStatus').dataset.mode==='"+mode+"'})()");
   if(!await setSaddle('saddle-narrow'))throw Error('real GLB narrow saddle contour unavailable');
   const narrowFrame=await capture();
   if(!await setSaddle('saddle-wide'))throw Error('real GLB wide saddle contour unavailable');
   const wideFrame=await capture();
   if(!await setSaddle('original'))throw Error('real GLB original saddle contour restoration unavailable');
   const exactSaddleRestored=await capture();
   if(originalPaint.equals(narrowFrame)||originalPaint.equals(wideFrame)||
      narrowFrame.equals(wideFrame))
     throw Error('real saddle contour hypotheses failed to change source GLB viewport pixels');
   if(!originalPaint.equals(exactSaddleRestored))
     throw Error('saddle contour preview did not restore exact original GLB canvas pixels');
   writeFileSync(join(out,'model-review-saddle-narrow-412.png'),narrowFrame);
   writeFileSync(join(out,'model-review-saddle-wide-412.png'),wideFrame);
   if(!await setSaddle('saddle-cup-deep'))throw Error('real GLB deeper saddle center cup unavailable');
   const deepCupFrame=await capture();
   if(!await setSaddle('saddle-cup-soft'))throw Error('real GLB softer saddle center cup unavailable');
   const softCupFrame=await capture();
   if(!await setSaddle('original'))throw Error('real GLB center cup original restoration unavailable');
   const exactCupRestored=await capture();
   if(originalPaint.equals(deepCupFrame)||originalPaint.equals(softCupFrame)||
      deepCupFrame.equals(softCupFrame))
     throw Error('center saddle cup changed no source-authenticated model viewport pixels');
   if(!originalPaint.equals(exactCupRestored))
     throw Error('saddle cup failed byte-identical GLB viewport restoration');
   writeFileSync(join(out,'model-review-saddle-cup-deep-412.png'),deepCupFrame);
   writeFileSync(join(out,'model-review-saddle-cup-soft-412.png'),softCupFrame);
   if(!await setSaddle('fork-crown-narrow'))throw Error('real GLB narrower fork crown unavailable');
   const narrowCrownFrame=await capture();
   if(!await setSaddle('fork-crown-full'))throw Error('real GLB fuller fork crown unavailable');
   const fullCrownFrame=await capture();
   if(!await setSaddle('original'))throw Error('real GLB original fork crown restoration unavailable');
   const restoredCrown=await capture();
   if(originalPaint.equals(narrowCrownFrame)||originalPaint.equals(fullCrownFrame)||
      narrowCrownFrame.equals(fullCrownFrame))
     throw Error('fork crown geometry alternatives produced no real GLB viewport difference');
   if(!originalPaint.equals(restoredCrown))
     throw Error('fork crown variant failed byte-identical original model restoration');
   writeFileSync(join(out,'model-review-fork-crown-narrow-412.png'),narrowCrownFrame);
   writeFileSync(join(out,'model-review-fork-crown-full-412.png'),fullCrownFrame);
   const setBlades=async mode=>evaluate("(()=>{const q=document.getElementById('bladeSpokes');if(q.disabled)return false;q.value='"+mode+"';q.dispatchEvent(new Event('change',{bubbles:true}));return q.value==='"+mode+"'&&document.getElementById('bladeSpokesStatus').dataset.mode==='"+mode+"'})()");
   if(!await setBlades('original'))throw Error('real original 2026 spoke mesh not available');
   // Freeze one identical camera, then compare the *actual* source GLB mesh.
   await capture();
   const normalBlades=await capture();
   if(!await setBlades('blade'))throw Error('wider source spoke volume unavailable');
   const broadBladePixels=await capture();
   if(!await setBlades('original'))throw Error('original 2026 spoke geometry restoration failed');
   const restoredBladePixels=await capture();
   if(normalBlades.equals(broadBladePixels))
     throw Error('real source 2026 spokes grew in label only, not rendered GLB pixels');
   if(!normalBlades.equals(restoredBladePixels))
     throw Error('wider spoke research preview failed pixel-identical GLB restoration');
   writeFileSync(join(out,'model-review-wheel-spokes-original-412.png'),normalBlades);
   writeFileSync(join(out,'model-review-wheel-spokes-wide-412.png'),broadBladePixels);
   // Check true source-verified three-dimensional dark housing, not merely
   // select values: rendered pixels must change in one fixed printed-hub-like
   // model view, then restore byte-identically. Neither camera nor shape
   // represents a recovered 1994 production mesh.
   const hubView=await evaluate("(()=>{const b=[...document.querySelectorAll('#views button')].find(x=>x.textContent==='Print hub');if(!b)return false;b.click();return document.getElementById('manualViewStatus').dataset.preset==='print-hub'})()");
   if(!hubView)throw Error('uncalibrated print hub camera inspection unavailable');
   await capture();
   const originalHub=await capture();
   const setHubFace=async mode=>evaluate("(()=>{const q=document.getElementById('hubFace');if(q.disabled)return false;q.value='"+mode+"';q.dispatchEvent(new Event('change',{bubbles:true}));return q.value==='"+mode+"'&&document.getElementById('hubFaceStatus').dataset.mode==='"+mode+"'})()");
   if(!await setHubFace('cover'))throw Error('source 2026 hub cover preview could not add closed 3D geometry');
   const coveredHub=await capture();
   if(!await setHubFace('original'))throw Error('source 2026 hub cover geometry could not reset');
   const restoredHub=await capture();
   if(originalHub.equals(coveredHub))
     throw Error('real source 2026 hub cover did not alter fixed-view GLB pixels');
   if(!originalHub.equals(restoredHub))
     throw Error('source 2026 dark hub cover did not restore exact GLB framebuffer');
   writeFileSync(join(out,'model-review-hub-cover-original-412.png'),originalHub);
   writeFileSync(join(out,'model-review-hub-cover-proposed-412.png'),coveredHub);
   const stepped=await evaluate("(()=>{const c=document.getElementById('crankScrub');if(c.disabled)return false;c.value='4';c.dispatchEvent(new Event('input',{bubbles:true}));return Number(document.getElementById('crankStatus').dataset.step)===4||Number(c.value)===4})()");
   if(!stepped)throw Error('source 2026 crank step for axle-locked housing unavailable');
   const originalAtPhase=await capture();
   if(!await setHubFace('cover'))throw Error('source wheel-rotating hub comparison unavailable');
   const rotatingAtPhase=await capture();
   if(!await setHubFace('axle-locked'))throw Error('source axle-locked 2026 hub preview not available');
   const lockedAtPhase=await capture();
   const axleDegrees=await evaluate("document.getElementById('hubFaceStatus').dataset.counterspinDegrees");
   // The browser smoke may be on any of the five authored GLB named poses.
   // Wheel phase = immutable named-pose offset PLUS 45 degrees of scrub.
   // Never assume the checked pose is upright or change the source pose to
   // accommodate a test expectation.
   const activePose=await evaluate("([...document.querySelectorAll('[id^=pose-]')].find(x=>x.getAttribute('aria-pressed')==='true')?.id||'').slice(5)");
   const expectedDegrees=sourcePhaseDelta(activePose,SOURCE_SHA)+45;
   if(Number(axleDegrees)!==expectedDegrees)
     throw Error('source axle-locked housing phase not coupled to existing crank and named pose: '+activePose+' measured '+axleDegrees+' expected '+expectedDegrees);
   if(rotatingAtPhase.equals(lockedAtPhase))
     throw Error('axle-locked hub and wheel-rotating hub did not differ at a genuine wheel phase');
   if(!await setHubFace('welded'))throw Error('one source 2026 physical welded hub mode unavailable');
   const weldedAtPhase=await capture();
   const weldedVertices=await evaluate("document.querySelector('[name=source-hub-count]')?.value||document.getElementById('hubFaceStatus').dataset.mode");
   if(weldedVertices!=='welded')
     throw Error('source 2026 welded mode did not select actual geometry');
   if(weldedAtPhase.equals(originalAtPhase))
     throw Error('one 2026 physical welded housing did not render');
   if(!await setHubFace('original'))throw Error('original GLB hub cannot restore from welded view');
   const restoredPhase=await capture();
   if(!originalAtPhase.equals(restoredPhase))
     throw Error('source 2026 welded housing failed exact in-memory rollback');
   writeFileSync(join(out,'model-review-hub-welded-45deg-412.png'),weldedAtPhase);
   writeFileSync(join(out,'model-review-hub-cover-rotating-45deg-412.png'),rotatingAtPhase);
   writeFileSync(join(out,'model-review-hub-cover-axle-locked-45deg-412.png'),lockedAtPhase);
   await evaluate("window.__urArt4kVisualReadback.resume()");
  }
  const shot=await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:false},session);
  writeFileSync(join(out,'model-review-'+width+'.png'),Buffer.from(shot.data,'base64'));
  summaries.push(report);console.log('MODEL_REVIEW_CHROMIUM '+JSON.stringify(report));
  if(report.issues.length)throw Error('Browser defects: '+report.issues.join('; '));
 }
 writeFileSync(join(out,'model-review-smoke.json'),JSON.stringify({synthetic_glb:mocked,original_sprite_frames:true,summaries},null,2));
 console.log('MODEL_REVIEW_BROWSER_SMOKE_PASS');
}finally{
 try{ws?.close()}catch{}
 chrome.kill('SIGTERM');server.close();
 await new Promise(done=>{if(chrome.exitCode!==null)return done();chrome.once('exit',done);setTimeout(done,1600)});
 try{rmSync(chromeDir,{recursive:true,force:true})}catch{}
}
