// Client-side helper for *local* official printed source crops only.
// NEVER identifies original 1994 3D coordinates, part ownership or camera.
export const SCHEMA="UR-ART4K-OFFICIAL-MANUAL-SPARSE-2D/1";
export const SOURCE_BLOB="a52da4f94a75e3e76fd61a759cb8e0c3a4fbc5d3";
export const PARTS=Object.freeze({
 wheel:Object.freeze(["wheel_left","wheel_right","wheel_top","wheel_bottom"]),
 hub:Object.freeze(["hub_left","hub_right","hub_top","hub_bottom"]),
 saddle:Object.freeze(["saddle_left","saddle_right","saddle_top","saddle_bottom"]),
 crown:Object.freeze(["crown_left","crown_right"]),
 fork:Object.freeze(["fork_left","fork_right"]),
 clamp:Object.freeze(["clamp_top","clamp_bottom"]),
 crank:Object.freeze(["crank_root","pedal_center"]),
});
export const FIGURES=Object.freeze([
 Object.freeze({id:"p14-twist-fork-front",page:14,angle:"front"}),
 Object.freeze({id:"p14-zee-flip-oblique",page:14,angle:"three-quarter"}),
 Object.freeze({id:"p15-mega-underside",page:15,angle:"three-quarter"}),
 Object.freeze({id:"p16-menu-saddle",page:16,angle:"three-quarter"}),
]);
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
function text(v,label,min=1){
 if(typeof v!=="string"||v.trim().length<min)throw Error(label+" must be supplied");
 return v.trim();
}
export function verifyReceipt(receipt){
 if(!receipt||receipt.schema!=="UR-ART4K-ORIGINAL-MANUAL-PRINT-CROPS/1"||
    receipt.source_git_blob_sha1!==SOURCE_BLOB||
    !/^[0-9a-f]{64}$/.test(receipt.source_pdf_sha256||"")||
    receipt.printed_manual_page_count!==40||receipt.render_dpi!==144||
    receipt.shipping_art_approved!==false||
    receipt.same_historical_3d_mesh_as_source_game_proven!==false||
    !Array.isArray(receipt.figures)||receipt.figures.length!==FIGURES.length)
  throw Error("not an exact-origin 1994 manual crop receipt");
 for(let i=0;i<FIGURES.length;i++){
  const f=receipt.figures[i],p=FIGURES[i];
  if(!f||f.reference_id!==p.id||f.original_printed_page!==p.page||
     f.approximate_print_view!==p.angle||
     f.crop_png!==p.id+".png"||
     !/^[a-f0-9]{64}$/.test(f.crop_png_sha256||"")||
     f.historical_3d_camera_or_material_identity_verified!==false||
     f.human_landmarks_measured!==false||
     !Array.isArray(f.page_crop_pixels_xyxy)||f.page_crop_pixels_xyxy.length!==4||
     f.page_crop_pixels_xyxy.some(v=>!Number.isInteger(v))||
     f.page_crop_pixels_xyxy[2]<=f.page_crop_pixels_xyxy[0]||
     f.page_crop_pixels_xyxy[3]<=f.page_crop_pixels_xyxy[1])
    throw Error("manual source figure/crop identity incorrect: "+p.id);
 }
 return receipt;
}
export function makeFigure(){
 return {visible_points:{},unmeasurable:{},perspective_and_occlusion_notes:""};
}
export function dimensions(receipt,name){
 verifyReceipt(receipt);
 const row=receipt.figures.find(f=>f.reference_id===name);
 if(!row)throw Error("unknown original printed figure");
 const [x0,y0,x1,y1]=row.page_crop_pixels_xyxy;
 return Object.freeze({width:x1-x0,height:y1-y0,sha256:row.crop_png_sha256});
}
export function nextLandmark(draft,group){
 const names=PARTS[group];if(!names)throw Error("unknown source part");
 const pts=draft.visible_points[group]||{};
 return names.find(name=>!own(pts,name))||null;
}
export function markPoint(draft,group,x,y,dim){
 const key=nextLandmark(draft,group);
 if(!key)throw Error("all source part point positions already marked");
 if(![x,y].every(v=>typeof v==="number"&&Number.isFinite(v))||
    !dim||!Number.isInteger(dim.width)||!Number.isInteger(dim.height)||
    !(0<=x&&x<dim.width&&0<=y&&y<dim.height))
  throw Error("point must fall inside the current exact source crop");
 const updated={...draft.visible_points,[group]:{
  ...(draft.visible_points[group]||{}),[key]:[
   Math.round(x*100)/100,Math.round(y*100)/100]}};
 const hidden={...draft.unmeasurable};delete hidden[group];
 return {...draft,visible_points:updated,unmeasurable:hidden};
}
export function markOccluded(draft,group,reason){
 if(!PARTS[group])throw Error("unknown source part");
 const explanation=text(reason,"real print occlusion",8);
 const visible={...draft.visible_points};delete visible[group];
 return {...draft,visible_points:visible,
         unmeasurable:{...draft.unmeasurable,[group]:explanation}};
}
export function clearPart(draft,group){
 if(!PARTS[group])throw Error("unknown source part");
 const visible={...draft.visible_points},hidden={...draft.unmeasurable};
 delete visible[group];delete hidden[group];
 return {...draft,visible_points:visible,unmeasurable:hidden};
}
function validGroup(group,raw){
 if(!raw||typeof raw!=="object"||Array.isArray(raw)||
    Object.keys(raw).length!==PARTS[group].length)throw Error(group+" is incomplete");
 for(const label of PARTS[group]){
  if(!own(raw,label)||!Array.isArray(raw[label])||raw[label].length!==2||
     raw[label].some(v=>typeof v!=="number"||!Number.isFinite(v)))
   throw Error("invalid measured printed coordinate "+label);
 }
 if(PARTS[group].length===4){
  const [l,r,t,b]=PARTS[group].map(k=>raw[k]);
  if(l[0]>=r[0]||t[1]>=b[1])throw Error(group+" printed bounds inverted");
 }else if(["crown","fork"].includes(group)){
  if(raw[PARTS[group][0]][0]>=raw[PARTS[group][1]][0])
   throw Error(group+" printed width inverted");
 }else if(group==="clamp"){
  if(raw.clamp_top[1]>=raw.clamp_bottom[1])
   throw Error("clamp printed top/bottom inverted");
 }
}
export function buildAnnotations(receipt,figures,annotator,uncertainty){
 verifyReceipt(receipt);
 const user=text(annotator,"annotator");
 if(user.startsWith("UNANNOTATED"))throw Error("actual original print reviewer required");
 if(!Number.isFinite(uncertainty)||uncertainty<=0||uncertainty>100)
  throw Error("nonzero bounded print pixel uncertainty required");
 const observations=[];
 for(const p of FIGURES){
  const state=figures[p.id];if(!state)continue;
  if(!state.visible_points||!state.unmeasurable)throw Error("invalid figure state");
  const present=Object.keys(state.visible_points);
  const hidden=Object.keys(state.unmeasurable);
  if(!present.length&&!hidden.length)continue;
  const known=Object.keys(PARTS);
  if(!present.length||present.some(k=>!known.includes(k))||
     hidden.some(k=>!known.includes(k))||
     present.some(k=>hidden.includes(k))||
     [...present,...hidden].length!==known.length)
    throw Error(p.id+": mark or explicitly hide all seven print part groups");
  const size=dimensions(receipt,p.id);
  for(const group of present){
   validGroup(group,state.visible_points[group]);
   for(const position of Object.values(state.visible_points[group]))
    if(position[0]<0||position[0]>=size.width||
       position[1]<0||position[1]>=size.height)
     throw Error("source point outside uploaded PNG");
  }
  for(const group of hidden)text(state.unmeasurable[group],"source occlusion "+group,8);
  const row=receipt.figures.find(f=>f.reference_id===p.id);
  observations.push({
   reference_id:p.id,crop_png_sha256:row.crop_png_sha256,
   annotator:user,pixel_uncertainty:Number(uncertainty),
   perspective_and_occlusion_notes:text(
    state.perspective_and_occlusion_notes,p.id+" perspective notes",12),
   visible_points:state.visible_points,unmeasurable:state.unmeasurable,
  });
 }
 if(!observations.length)throw Error("annotate at least one genuine visible part");
 return {
  schema:SCHEMA,source_pdf_sha256:receipt.source_pdf_sha256,
  annotations:observations,
 };
}
