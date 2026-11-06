import test from "node:test";
import assert from "node:assert/strict";
import {FIGURES,PARTS,SOURCE_BLOB,makeFigure,markOccluded,
        addVisibleSurfaceRegion,clearVisibleSurfaceRegions,buildAnnotations}
 from "./manual_landmark_marking.mjs";

const SIZE={width:200,height:200};
function receipt(){
 return {schema:"UR-ART4K-ORIGINAL-MANUAL-PRINT-CROPS/1",
  source_git_blob_sha1:SOURCE_BLOB,source_pdf_sha256:"a".repeat(64),
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
const surface={
 region_id:"near-side-hub-cover",
 visible_appearance_notes:"Visible printed dark cover face, no known source ownership",
 cutoff_or_occlusion_notes:"Original printed wheel and fork obscure the remainder",
 visible_polygon_xy:[[20,25],[120,25],[115,140],[25,145]],
 original_3d_part_identity_verified:false,
 entire_original_3d_surface_visible:false,
};
test("local source-only polygon with no complete 3D hub is exportable",()=>{
 let draft=makeFigure();
 draft=addVisibleSurfaceRegion(draft,surface,SIZE);
 for(const name of Object.keys(PARTS))
  draft=markOccluded(draft,name,"Source part occluded outside one visible patch");
 draft.perspective_and_occlusion_notes="Oblique original print; actual artist camera unknown";
 const report=buildAnnotations(receipt(),{[FIGURES[2].id]:draft},"source pixel observer",10);
 assert.equal(report.annotations.length,1);
 assert.equal(report.annotations[0].reference_id,"p15-mega-underside");
 assert.deepEqual(report.annotations[0].visible_surface_regions,[surface]);
 assert.deepEqual(report.annotations[0].visible_points,{});
 assert.ok("hub" in report.annotations[0].unmeasurable);
 assert.ok(!("original_1994_3d_mesh_recovered" in report));
 const cleared=clearVisibleSurfaceRegions(draft);
 assert.deepEqual(cleared.visible_surface_regions,[]);
 assert.throws(()=>buildAnnotations(receipt(),{[FIGURES[2].id]:cleared},
                                    "source pixel observer",10),/mark or explicitly/);
});
test("wrong partial original print attribution, polygon or coordinate fails closed",()=>{
 const bad=[
  {...surface,original_3d_part_identity_verified:true},
  {...surface,entire_original_3d_surface_visible:true},
  {...surface,region_id:"1994 3D hub mesh"},
  {...surface,visible_polygon_xy:[[5,5],[10,10],[15,15]]},
  {...surface,visible_polygon_xy:[[5,5],[50,50],[5,50],[50,5]]},
  {...surface,visible_polygon_xy:[[5,5],[200,10],[10,50]]},
  {...surface,visible_polygon_xy:[[5,5],[10,50]]},
  {...surface,cutoff_or_occlusion_notes:"?"}
 ];
 for(const example of bad)assert.throws(()=>addVisibleSurfaceRegion(makeFigure(),example,SIZE));
 let draft=addVisibleSurfaceRegion(makeFigure(),surface,SIZE);
 assert.throws(()=>addVisibleSurfaceRegion(draft,surface,SIZE),/uniquely named/);
 const other={...surface,region_id:"another-source-face"};
 draft=addVisibleSurfaceRegion(draft,other,SIZE);
 assert.equal(draft.visible_surface_regions.length,2);
});
