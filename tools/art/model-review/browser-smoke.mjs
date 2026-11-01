#!/usr/bin/env node
// Browser acceptance: 1994 sprite rail + actual WebGL pose GLB, mobile and desktop.
// Uses Chrome DevTools directly. No npm dependencies or source ROM are needed.
import {createServer} from 'node:http';
import {spawn} from 'node:child_process';
import {readFileSync,existsSync,mkdirSync,writeFileSync,mkdtempSync,rmSync} from 'node:fs';
import {resolve,join,sep} from 'node:path';
import {tmpdir} from 'node:os';

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
let mocked=false;
const original=JSON.parse(readFileSync(join(site,'model-review/manifest.json'),'utf8'));
const modelManifest={...original,version:'SYNTHETIC BROWSER FIXTURE',model_url:'mock.glb',
  poses:Object.fromEntries(['upright','pedal','wheelie','stunt','bank'].map(p=>[p,{url:'mock.glb'}])),
  likeness_approved:false};
const mime={html:'text/html; charset=utf-8',js:'application/javascript; charset=utf-8',css:'text/css; charset=utf-8',json:'application/json; charset=utf-8',png:'image/png',glb:'model/gltf-binary',svg:'image/svg+xml'};
const server=createServer((req,res)=>{
  let path;
  try{path=decodeURIComponent((req.url||'/').split('?')[0])}catch{res.writeHead(400);res.end();return}
  if(mocked&&path==='/model-review/manifest.json'){
    res.writeHead(200,{'Content-Type':mime.json,'Cache-Control':'no-store'});res.end(JSON.stringify(modelManifest));return}
  if(path==='/model-review/mock.glb'){
    res.writeHead(200,{'Content-Type':mime.glb});res.end(fakeGlb);return}
  const file=resolve(site,'.'+(path.endsWith('/')?path+'index.html':path));
  if(!file.startsWith(site+sep)){res.writeHead(403);res.end();return}
  try{res.writeHead(200,{'Content-Type':mime[file.split('.').at(-1)]||'application/octet-stream','Cache-Control':'no-store'});res.end(readFileSync(file))}
  catch{res.writeHead(404);res.end('missing')}
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
  mocked=true;
  await cdp('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<600},session);
  await cdp('Page.navigate',{url:address},session);
  let ready=false;
  for(let i=0;i<150;i++){
   ready=await evaluate("document.getElementById('source')?.textContent.includes('published current model') && document.getElementById('sprite')?.naturalWidth===64");
   if(ready)break;await sleep(100);
  }
  if(!ready)throw Error('Model/sprite did not load at '+width+'px; state '+await evaluate("document.getElementById('state')?.textContent"));
  const report=await evaluate(`(async function(){
   const issues=[],q=id=>document.getElementById(id),w=innerWidth;
   if(document.documentElement.scrollWidth>w+1)issues.push('horizontal overflow');
   if(!document.querySelector('#viewport canvas'))issues.push('no WebGL canvas');
   if(!q('parts').textContent.includes('tire'))issues.push('no glTF part');
   if(!q('sourceInfo').textContent.includes('frame 1205'))issues.push('missing original provenance');
   q('frame').value='1210';q('frame').dispatchEvent(new Event('input'));
   if(!q('sourceInfo').textContent.includes('frame 1210'))issues.push('sprite scrub');
   q('pose-bank').click();
   for(let i=0;i<100 && !q('source').textContent.includes('published bank GLB');i++)await new Promise(done=>setTimeout(done,50));
   if(!q('source').textContent.includes('published bank GLB'))issues.push('pose switch');
   q('wire').click();if(q('wire').getAttribute('aria-pressed')!=='true')issues.push('wireframe');
   q('spin').click();if(q('spin').getAttribute('aria-pressed')!=='true')issues.push('orbit');
   q('zup').click();if(q('zup').checked)issues.push('up-axis');
   return {width:w,height:innerHeight,issues,source:q('sourceInfo').textContent.slice(0,85)};
  })()`);
  const shot=await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:false},session);
  writeFileSync(join(out,'model-review-'+width+'.png'),Buffer.from(shot.data,'base64'));
  summaries.push(report);console.log('MODEL_REVIEW_CHROMIUM '+JSON.stringify(report));
  if(report.issues.length)throw Error('Browser defects: '+report.issues.join('; '));
 }
 writeFileSync(join(out,'model-review-smoke.json'),JSON.stringify({synthetic_glb:true,original_sprite_frames:true,summaries},null,2));
 console.log('MODEL_REVIEW_BROWSER_SMOKE_PASS');
}finally{
 try{ws?.close()}catch{}
 chrome.kill('SIGTERM');server.close();
 await new Promise(done=>{if(chrome.exitCode!==null)return done();chrome.once('exit',done);setTimeout(done,1600)});
 try{rmSync(chromeDir,{recursive:true,force:true})}catch{}
}
