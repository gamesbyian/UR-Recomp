import test from "node:test";
import assert from "node:assert/strict";
import {FIGURES,PARTS,SOURCE_BLOB,SCHEMA,makeFigure,verifyReceipt,dimensions,
        markPoint,markOccluded,clearPart,nextLandmark,buildAnnotations}
 from "./manual_landmark_marking.mjs";

const SHA="a".repeat(64);
function receipt(){
 return {schema:"UR-ART4K-ORIGINAL-MANUAL-PRINT-CROPS/1",
  source_git_blob_sha1:SOURCE_BLOB,source_pdf_sha256:SHA,
  printed_manual_page_count:40,render_dpi:144,
  same_historical_3d_mesh_as_source_game_proven:false,
  shipping_art_approved:false,
  figures:FIGURES.map(p=>({
   reference_id:p.id,original_printed_page:p.page,
   approximate_print_view:p.angle,crop_png:p.id+".png",
   crop_png_sha256:"b".repeat(64),
   page_crop_pixels_xyxy:[5,10,205,210],
   historical_3d_camera_or_material_identity_verified:false,
   human_landmarks_measured:false,
  }))};
}
test("frozen original four printed figures and source PNG SHA",()=>{
 const r=verifyReceipt(receipt());
 assert.equal(r.source_pdf_sha256,SHA);
 assert.equal(FIGURES.length,4);
 assert.equal(Object.keys(PARTS).length,7);
 assert.deepEqual(dimensions(r,FIGURES[0].id),{
  width:200,height:200,sha256:"b".repeat(64)});
 for(const field of ["source_git_blob_sha1","source_pdf_sha256",
                     "original_printed_page","crop_png_sha256"]){
  const copy=JSON.parse(JSON.stringify(r));
  if(field.startsWith("source_"))copy[field]="bad";
  else copy.figures[0][field]="bad";
  assert.throws(()=>verifyReceipt(copy));
 }
});
test("partial fork/crown measurement stays partial; invisible wheel ratio not inferred",()=>{
 const r=receipt(),id=FIGURES[0].id;
 let draft=makeFigure();
 assert.equal(nextLandmark(draft,"crown"),"crown_left");
 draft=markPoint(draft,"crown",10,20,{width:200,height:200});
 assert.equal(nextLandmark(draft,"crown"),"crown_right");
 draft=markPoint(draft,"crown",110,25,{width:200,height:200});
 assert.equal(nextLandmark(draft,"crown"),null);
 for(const part of Object.keys(PARTS).filter(x=>x!=="crown"))
  draft=markOccluded(draft,part,"Part hidden behind printed ribbon or paper crop");
 draft.perspective_and_occlusion_notes="Perspective uncalibrated; track ribbon occludes wheel.";
 const report=buildAnnotations(r,{[id]:draft},"observant reviewer",2.5);
 assert.equal(report.schema,SCHEMA);
 assert.equal(report.annotations.length,1);
 assert.equal(report.annotations[0].reference_id,id);
 assert.equal(report.annotations[0].crop_png_sha256,"b".repeat(64));
 assert.deepEqual(report.annotations[0].visible_points.crown,{
  crown_left:[10,20],crown_right:[110,25]});
 assert.ok(!("wheel" in report.annotations[0].visible_points));
 assert.ok("wheel" in report.annotations[0].unmeasurable);
 assert.equal(report.annotations[0].pixel_uncertainty,2.5);
 assert.throws(()=>buildAnnotations(r,{[id]:draft},"UNANNOTATED",2.5),/reviewer/);
});
test("untouched/incomplete/forged/manual-1994-camera claims are rejected",()=>{
 const r=receipt(),id=FIGURES[1].id;
 assert.throws(()=>buildAnnotations(r,{},"a",2));
 let draft=makeFigure();
 draft=markPoint(draft,"fork",10,10,{width:200,height:200});
 draft.perspective_and_occlusion_notes="Only near-side fork is visible.";
 assert.throws(()=>buildAnnotations(r,{[id]:draft},"observer",2),/mark or explicitly/);
 assert.throws(()=>markPoint(draft,"fork",-1,10,{width:200,height:200}));
 assert.throws(()=>markPoint(draft,"fork",Number.NaN,10,{width:200,height:200}));
 assert.throws(()=>markOccluded(draft,"wheel","hidden"),/occlusion/);
 assert.throws(()=>buildAnnotations(r,{[id]:draft},"UNANNOTATED",0));
 draft=markOccluded(draft,"fork","Obscured by original printed track");
 assert.equal(nextLandmark(draft,"fork"),"fork_left");
 draft=clearPart(draft,"fork");
 assert.equal(Object.keys(draft.visible_points).length,0);
 assert.equal(Object.keys(draft.unmeasurable).length,0);
});
