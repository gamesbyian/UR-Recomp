#!/usr/bin/env node
// ROM-free browser QA: real mobile viewports, interaction smoke and inspectable PNGs.
// No npm packages; speaks directly to Chromium's native DevTools protocol.
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { readFileSync, existsSync, mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { resolve, join, sep } from 'node:path';
import { tmpdir } from 'node:os';

const site=resolve(process.argv[2]||'.'),output=resolve(process.argv[3]||'.');
if(!existsSync(join(site,'atlas.json')))throw Error('Build the atlas website first');
mkdirSync(output,{recursive:true});
const mime={html:'text/html; charset=utf-8',js:'application/javascript; charset=utf-8',css:'text/css; charset=utf-8',json:'application/json; charset=utf-8',png:'image/png',svg:'image/svg+xml'};
const server=createServer((req,res)=>{
  const pathname=decodeURIComponent((req.url||'/').split('?')[0]);
  const file=resolve(site,'.'+(pathname==='/'?'/index.html':pathname));
  if(!file.startsWith(site+sep)){res.writeHead(403);res.end();return}
  let payload;
  try{payload=readFileSync(file)}
  catch(_){res.writeHead(404);res.end('missing');return}
  res.writeHead(200,{'Content-Type':mime[file.split('.').at(-1)]||'application/octet-stream','Cache-Control':'no-store'});
  res.end(payload);
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const address='http://127.0.0.1:'+server.address().port+'/';
const chromeProfile=mkdtempSync(join(tmpdir(),'ur-atlas-optical-'));
// Reserve an ephemeral port: runner Chrome variants do not always write DevToolsActivePort.
const probe=createServer();
await new Promise(resolve=>probe.listen(0,'127.0.0.1',resolve));
const debugPort=probe.address().port;
await new Promise(resolve=>probe.close(resolve));
let chromeErrors='';
const chrome=spawn(process.env.CHROME_BIN||'/usr/bin/google-chrome',[
  '--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
  '--no-first-run','--no-default-browser-check','--disable-extensions',
  '--no-proxy-server','--remote-debugging-port='+debugPort,
  '--user-data-dir='+chromeProfile,'about:blank'
],{stdio:['ignore','ignore','pipe']});
chrome.stderr?.on('data',chunk=>{chromeErrors=(chromeErrors+String(chunk)).slice(-4000)});
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const awaiting=new Map();
let ws,session,sequence=0;
function cdp(method,params={},sessionId){
  return new Promise((resolve,reject)=>{
    const id=++sequence;
    const timeout=setTimeout(()=>{awaiting.delete(id);reject(Error('CDP timeout: '+method))},12000);
    awaiting.set(id,{
      resolve(value){clearTimeout(timeout);resolve(value)},
      reject(error){clearTimeout(timeout);reject(error)}
    });
    ws.send(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})}));
  });
}
async function runScript(expression){
  const response=await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},session);
  if(response.exceptionDetails)throw Error('Browser script exception: '+JSON.stringify(response.exceptionDetails).slice(0,650));
  return response.result?.value;
}
const summary=[];
try{
  let endpoint='', connectionProblem='';
  for(let tick=0;tick<300;tick++){
    if(chrome.exitCode!==null)break;
    try{
      const response=await fetch('http://127.0.0.1:'+debugPort+'/json/version');
      if(response.ok){
        endpoint=(await response.json()).webSocketDebuggerUrl;
        if(endpoint)break;
      }
    }catch(error){ connectionProblem=String(error); /* Chrome has not started listening yet. */ }
    await pause(100);
  }
  if(!endpoint)throw Error('Chromium debugger did not start; port='+debugPort+' exit='+chrome.exitCode+' lastHTTP='+connectionProblem+' stderr='+chromeErrors.slice(-1600));
  ws=new WebSocket(endpoint);
  await new Promise((resolve,reject)=>{
    ws.addEventListener('open',resolve,{once:true});
    ws.addEventListener('error',reject,{once:true});
  });
  ws.addEventListener('message',event=>{
    let message;
    try{message=JSON.parse(event.data)}catch(_){return}
    const waiter=awaiting.get(message.id);
    if(!waiter)return;
    awaiting.delete(message.id);
    if(message.error)waiter.reject(Error(message.error.message));else waiter.resolve(message.result||{});
  });
  const target=await cdp('Target.createTarget',{url:'about:blank'});
  session=(await cdp('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;
  await cdp('Page.enable',{},session);
  await cdp('Runtime.enable',{},session);
  const manifest=JSON.parse(readFileSync(join(site,'atlas.json'),'utf8'));
  const total=manifest.entries.length;
  if(total<50)throw Error('Unexpected atlas inventory size: '+total);
  for(const [width,height] of [[320,720],[393,852],[430,932],[768,1024],[1440,900]]){
    await cdp('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<=430},session);
    await cdp('Emulation.setTouchEmulationEnabled',{enabled:width<=430,maxTouchPoints:1},session);
    await cdp('Page.navigate',{url:address},session);
    let ready=false;
    for(let attempt=0;attempt<90;attempt++){
      ready=await runScript("document.querySelectorAll('.tile').length === "+total);
      if(ready)break;
      await pause(100);
    }
    if(!ready)throw Error('Viewport '+width+': atlas gallery failed to render '+total+' cases');
    const report=await runScript("(function(){"+
      "const issues=[];const w=innerWidth,scroll=document.documentElement.scrollWidth;"+
      "if(scroll>w+1)issues.push('horizontal overflow '+scroll+' > '+w);"+
      "const count=document.querySelectorAll('.tile').length;"+
      "if(count!=="+total+")issues.push('wrong inventory count '+count);"+
      "for(const id of ['search','mode','family','status','evidence','view-list','view-grid','detail','copy-ref'])"+
      "if(!document.getElementById(id))issues.push('missing '+id);"+
      "document.getElementById('view-grid').click();"+
      "if(!document.getElementById('gallery').classList.contains('grid-view'))issues.push('grid toggle');"+
      "document.getElementById('view-list').click();"+
      "const search=document.getElementById('search');search.value='URV-MD-001';"+
      "search.dispatchEvent(new Event('input',{bubbles:true}));"+
      "if(document.querySelectorAll('.tile').length!==1)issues.push('ID lookup');"+
      "search.value='';search.dispatchEvent(new Event('input',{bubbles:true}));"+
      "const evidence=document.getElementById('evidence');evidence.value='original';"+
      "evidence.dispatchEvent(new Event('input',{bubbles:true}));"+
      "const original=document.querySelectorAll('.tile').length;"+
      "if(original!==120)issues.push('original UI anchor filter '+original);"+
      "evidence.value='';evidence.dispatchEvent(new Event('input',{bubbles:true}));"+
      "document.querySelector('.tile .preview').click();"+
      "const dialog=document.getElementById('detail');"+
      "if(!dialog.open)issues.push('inspect dialog');"+
      "if(!location.hash.startsWith('#URV-'))issues.push('stable link');"+
      "if(!document.getElementById('detail-evidence').textContent)issues.push('missing provenance');"+
      "document.getElementById('close').click();"+
      "if(dialog.open)issues.push('dialog close');"+
      "document.querySelector('.card-select input').click();"+
      "if(document.getElementById('selection-bar').hidden)issues.push('multi-copy selection');"+
      "document.getElementById('selection-clear').click();"+
      "if(!document.getElementById('selection-bar').hidden)issues.push('multi-copy clear');"+
      "return {width:w,height:innerHeight,scroll,count,original,issues};"+
      "})()");
    const gallery=await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:false},session);
    writeFileSync(join(output,'atlas-gallery-'+width+'.png'),Buffer.from(gallery.data,'base64'));
    await runScript("document.querySelector('.tile .preview').click()");
    const inspector=await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:false},session);
    writeFileSync(join(output,'atlas-inspector-'+width+'.png'),Buffer.from(inspector.data,'base64'));
    summary.push(report);
    console.log('Atlas browser '+width+'px: '+JSON.stringify(report));
    if(report.issues.length)throw Error('Browser defects at '+width+'px: '+report.issues.join('; '));
  }
  writeFileSync(join(output,'browser-smoke.json'),JSON.stringify({source:process.env.GITHUB_SHA||'local',total,summary},null,2)+'\n');
  console.log('ATLAS_BROWSER_SMOKE_PASS');
}finally{
  try{ws?.close()}catch(_){}
  chrome.kill('SIGTERM');
  server.close();
  await new Promise(resolve=>{
    if(chrome.exitCode!==null)return resolve();
    chrome.once('exit',resolve);
    setTimeout(resolve,1800);
  });
  try{rmSync(chromeProfile,{recursive:true,force:true})}catch(error){console.warn('Temp profile cleanup:',error.code)}
}
