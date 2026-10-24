"use strict";
(() => {
 const $=id=>document.getElementById(id);
 const labels={captured:"REAL CAPTURE",capture_pending:"CAPTURE PENDING",capture_failed:"CAPTURE FAILED",planned:"COMING SOON"};
 const modes={modern:"Modern",authentic:"Authentic","original-4x":"Original 4×",remastered:"Remastered",widescreen:"Widescreen",future:"Planned"};
 const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
 const valid=id=>/^URV-[A-Z]{2,3}-[0-9]{3}$/.test(id);
 const mode=e=>modes[e.mode]||e.mode;
 const art=e=>"./assets/"+encodeURIComponent(e.art)+".png";
 const image=e=>e.status==="captured"?"./"+e.image:art(e);
 const type=e=>{
   if(e.status==="captured"&&e.evidence?.actual_sdl_final_drawable===true)return ["windows","WINDOWS SDL · SOURCE-BOUND"];
   if(e.source_inventory?.path==="analysis/ui-capture-manifest.json")return ["original","ORIGINAL UI ANCHOR · NO WIN32 FRAME"];
   if(e.source_inventory?.path==="analysis/modern-visual-acceptance-matrix.json")return ["qa","QA CASE · NO WIN32 FRAME"];
   return ["concept",e.capture?"NATIVE ROUTE · UNCAPTURED":"EDITORIAL PLATE · NO CAPTURE"];
 };
 const source=e=>{
   const path=e.source_inventory?.path||(e.capture?.route?"tools/qa_modern_visual_win32_capture_driver.py":null);
   if(!path||!/^(tools|analysis)\/[\w./-]+$/.test(path)||path.includes(".."))return "";
   const sha=/^[a-f0-9]{40}$/.test(e.evidence?.source_sha||"")?e.evidence.source_sha:"main";
   return "https://github.com/gamesbyian/UR-Recomp/blob/"+sha+"/"+path.split("/").map(encodeURIComponent).join("/");
 };
 const permalink=e=>/^https?:$/.test(location.protocol)?location.href.split("#")[0]+"#"+e.id:"";
 const reference=e=>{
   const evidence=e.evidence?"Observed Windows final SDL drawable; source "+e.evidence.source_sha+
      "; EXE SHA256 "+e.evidence.exe_sha256+"; PNG SHA256 "+e.evidence.png_sha256+
      "; physical/art/release acceptance not implied.":"NO Windows capture; "+labels[e.status]+
      "; the graph-paper image is editorial, not software evidence.";
   const provenance=e.source_inventory?" Source inventory "+e.source_inventory.path+" / "+
      (e.source_inventory.tag||e.source_inventory.acceptance_case_id)+".":"";
   const route=e.capture?" Native route "+e.capture.route+" @ "+e.capture.size+".":"";
   return "Inspect "+e.id+" ("+e.title+"). "+mode(e)+" / "+e.family+" / "+e.state+
      " / "+e.display+". "+evidence+provenance+route+
      (permalink(e)?" Atlas: "+permalink(e):" Atlas ID: "+e.id);
 };
 let entries=[],shown=[],current=null,oldFocus=null,downX=null,layout="list";
 const selected=new Set();
 async function copy(text,element){
   let good=false;
   try{if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(text);good=true}}catch(_){}
   if(!good){const el=document.createElement("textarea");el.value=text;el.readOnly=true;el.style.cssText="position:fixed;left:-9999px";document.body.append(el);el.select();
     try{good=document.execCommand("copy")}catch(_){}el.remove()}
   if(!good){window.prompt("Copy this atlas reference:",text);return}
   if(element){const before=element.textContent;element.textContent="Copied ✓";
     if(element.tagName==="BUTTON")setTimeout(()=>element.textContent=before,1300)}
 }
 function option(el,value,label){const item=document.createElement("option");item.value=value;item.textContent=label;el.append(item)}
 function filter(){
   const q=$("search").value.trim().toLowerCase(),m=$("mode").value,f=$("family").value,
     s=$("status").value,ev=$("evidence").value,sort=$("sort").value;
   const list=entries.filter(e=>(!m||m===e.mode)&&(!f||f===e.family)&&(!s||s===e.status)&&(!ev||ev===type(e)[0])&&
     (!q||[e.id,e.title,e.mode,e.family,e.state,e.display,e.capture?.route,e.source_inventory?.tag,
       e.source_inventory?.acceptance_case_id].filter(Boolean).join(" ").toLowerCase().includes(q)));
   const key=e=>sort==="title"?e.title:sort==="family"?e.family:sort==="status"?e.status:e.id;
   list.sort((a,b)=>key(a).localeCompare(key(b),undefined,{numeric:true})||a.id.localeCompare(b.id));return list;
 }
 function countSelected(){
   const n=selected.size;$("selection-bar").hidden=n===0;$("selection-count").textContent=n+" selected";
   $("selection-copy").textContent="▣ Copy "+n+" reference"+(n===1?"":"s");
 }
 function render(){
   shown=filter();
   $("result-count").textContent=shown.length+" / "+entries.length+" references";
   const n=entries.filter(e=>e.status==="captured").length;
   $("summary").textContent=n+" source-bound Windows captures · "+(entries.length-n)+" without a native frame";
   const host=$("gallery");host.className="gallery "+layout+"-view";host.replaceChildren();
   if(!shown.length){const p=document.createElement("p");p.className="loading";p.textContent="No matches. Clear filters to see the full atlas.";host.append(p);return}
   const frag=document.createDocumentFragment();
   for(const e of shown){
     const row=document.createElement("article");row.className="tile";row.dataset.status=e.status;
     const link=source(e),isReal=e.status==="captured";
     row.innerHTML='<button class="preview" type="button" aria-label="Inspect '+esc(e.id+": "+e.title)+'"><img loading="lazy" decoding="async" src="'+esc(image(e))+'" alt="'+esc((isReal?"Native Windows screenshot: ":"Illustrated graph-paper plate, not a capture: ")+e.title)+'"><span class="status-ribbon">'+esc(labels[e.status])+'</span></button>'+
      '<div class="tile-description"><div class="tile-top"><span class="tile-id">'+esc(e.id)+'</span>'+
      '<label class="card-select" title="Select for batch copy"><input type="checkbox" '+(selected.has(e.id)?"checked ":"")+'aria-label="Select '+esc(e.id)+' for batch reference copy"></label></div>'+
      '<h2><button class="tile-open" type="button">'+esc(e.title)+'</button></h2>'+
      '<p class="tile-state">'+esc(e.state+" · "+e.display)+'</p>'+
      '<div class="tag-group"><span class="tag">'+esc(mode(e))+'</span><span class="tag family">'+esc(e.family)+'</span></div>'+
      '<div class="evidence-line">'+esc(type(e)[1])+'</div><div class="tile-foot">'+
      '<button class="copy-small" type="button" aria-label="Copy reference '+esc(e.id)+'">▣ Copy ref</button>'+
      (link?'<a href="'+esc(link)+'" target="_blank" rel="noopener noreferrer">↗ Source</a>':'')+'</div></div>';
     row.querySelector(".preview").addEventListener("click",()=>open(e));
     row.querySelector(".tile-open").addEventListener("click",()=>open(e));
     row.querySelector(".copy-small").addEventListener("click",ev=>copy(reference(e),ev.currentTarget));
     row.querySelector(".card-select input").addEventListener("change",ev=>{ev.target.checked?selected.add(e.id):selected.delete(e.id);countSelected()});
     frag.append(row);
   }
   host.append(frag);
 }
 function setView(next){layout=next;for(const v of ["grid","list"]){$("view-"+v).classList.toggle("active",v===next);$("view-"+v).setAttribute("aria-pressed",String(v===next))}render()}
 function updateDetail(e){
   current=e;
   $("detail-id").textContent=e.id;$("detail-reference-id").textContent=e.id;
   $("detail-number").textContent=(shown.findIndex(x=>x.id===e.id)+1)+" / "+shown.length;
   $("detail-title").textContent=e.title;
   $("detail-meta").textContent=[mode(e),e.family,e.state,e.display].join(" · ");
   $("detail-mode").textContent=mode(e);$("detail-family").textContent=e.family;
   $("detail-state").textContent=e.state;$("detail-display").textContent=e.display;
   $("detail-status").textContent=labels[e.status];
   $("detail-status").style.background={captured:"var(--green)",capture_pending:"var(--yellow)",capture_failed:"var(--coral)",planned:"var(--violet)"}[e.status];
   $("detail-evidence-type").textContent=type(e)[1];
   $("detail-provenance").textContent=e.status==="captured"?
      "Actual native Windows final SDL drawable. Source/EXE/PNG identities recorded; no hardware, original parity, art or release approval.":
      "Graph-paper promotional artwork only. "+labels[e.status]+": this atlas slot has no admitted Windows screenshot.";
   $("detail-evidence").textContent=JSON.stringify(e.evidence||{capture_status:e.status,source_inventory:e.source_inventory||null,planned_route:e.capture||null,release_gate_credit:0},null,2);
   const link=source(e);$("open-source").hidden=!link;if(link)$("open-source").href=link;
   $("zoom").disabled=e.status!=="captured";$("zoom").textContent="1:1 pixels";
   const stage=$("image-stage");stage.classList.remove("native");stage.replaceChildren();
   const img=new Image();img.src=image(e);img.alt=e.status==="captured"?"Actual SDL screenshot":"Graph-paper editorial drawing, not Windows software";
   if(e.status==="captured")stage.append(img);
   else{const box=document.createElement("div");box.className="placeholder";const label=document.createElement("strong");label.textContent=labels[e.status];box.append(img,label);stage.append(box)}
   $("copy-status").textContent="";
 }
 function open(e,updateHash=true){
   if(!valid(e.id))return;
   if(!$("detail").open)oldFocus=document.activeElement;
   updateDetail(e);
   if(!$("detail").open)$("detail").showModal();
   if(updateHash&&location.hash!=="#"+e.id)history.pushState(null,"","#"+e.id);
   $("close").focus({preventScroll:true});
 }
 function close(rewrite=true){
   if($("detail").open)$("detail").close();current=null;
   if(rewrite&&location.hash.startsWith("#URV-"))history.replaceState(null,"",location.pathname+location.search);
   if(oldFocus?.isConnected)oldFocus.focus({preventScroll:true});oldFocus=null;
 }
 function navigate(n){const i=shown.findIndex(e=>e.id===current?.id);if(i>=0&&shown.length>1)open(shown[(i+n+shown.length)%shown.length])}
 function followHash(){
   const id=location.hash.slice(1);
   const row=valid(id)?entries.find(e=>e.id===id):null;
   if(row)open(row,false);else if($("detail").open)close(false);
 }
 async function init(){
   try{
     const response=await fetch("./atlas.json",{cache:"no-cache"});
     if(!response.ok)throw Error("HTTP "+response.status);
     const data=await response.json();
     if(data.schema_version!==1||!Array.isArray(data.entries))throw Error("Unsupported inventory");
     entries=data.entries.filter(e=>valid(e.id)&&labels[e.status]&&e.art);
     for(const m of [...new Set(entries.map(e=>e.mode))].sort())option($("mode"),m,modes[m]||m);
     for(const f of [...new Set(entries.map(e=>e.family))].sort())option($("family"),f,f);
     for(const id of ["search","mode","family","status","evidence","sort"])$(id).addEventListener("input",render);
     $("reset-filters").addEventListener("click",()=>{for(const id of ["search","mode","family","status","evidence"])$(id).value="";render();$("search").focus()});
     $("view-list").addEventListener("click",()=>setView("list"));
     $("view-grid").addEventListener("click",()=>setView("grid"));
     $("selection-clear").addEventListener("click",()=>{selected.clear();countSelected();render()});
     $("selection-copy").addEventListener("click",ev=>{const lines=[...selected].map(id=>entries.find(e=>e.id===id)).filter(Boolean).map(reference);if(lines.length)copy(lines.join("\n\n"),ev.currentTarget)});
     setView("list");countSelected();followHash();
   }catch(e){$("result-count").textContent="Atlas unavailable";$("summary").textContent="";$("gallery").textContent="Unable to read atlas.json: "+e.message+". Serve the assembled static site over HTTP."}
 }
 $("close").addEventListener("click",()=>close());
 $("detail").addEventListener("cancel",ev=>{ev.preventDefault();close()});
 $("copy-ref").addEventListener("click",ev=>current&&copy(reference(current),ev.currentTarget));
 $("copy-link").addEventListener("click",ev=>current&&copy(permalink(current)||current.id,ev.currentTarget));
 $("zoom").addEventListener("click",()=>{if(current?.status!=="captured")return;const active=$("image-stage").classList.toggle("native");$("zoom").textContent=active?"Fit image":"1:1 pixels"});
 $("prev").addEventListener("click",()=>navigate(-1));$("next").addEventListener("click",()=>navigate(1));
 $("image-stage").addEventListener("touchstart",e=>downX=e.touches[0]?.clientX??null,{passive:true});
 $("image-stage").addEventListener("touchend",e=>{if(downX===null)return;const delta=(e.changedTouches[0]?.clientX??downX)-downX;downX=null;if(!$("image-stage").classList.contains("native")&&Math.abs(delta)>75)navigate(delta>0?-1:1)},{passive:true});
 document.addEventListener("keydown",e=>{if(!$("detail").open||e.target.matches("input,textarea,select"))return;if(e.key==="ArrowRight"){e.preventDefault();navigate(1)}if(e.key==="ArrowLeft"){e.preventDefault();navigate(-1)}});
 window.addEventListener("popstate",followHash);window.addEventListener("hashchange",followHash);
 init();
})();
