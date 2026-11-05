// Reversible, manual-INSPIRED views of the one unapproved 2026 GLB.
// The actual 1994 print rendering cameras, optics and model are unknown.
export const CAMERA_VIEW_PRESETS=Object.freeze([
 Object.freeze({id:"side",label:"Side",direction:[0,0,1],printedPage:null}),
 Object.freeze({id:"reverse",label:"Reverse",direction:[0,0,-1],printedPage:null}),
 Object.freeze({id:"front",label:"Front",direction:[1,0,0],printedPage:null}),
 Object.freeze({id:"back",label:"Back",direction:[-1,0,0],printedPage:null}),
 Object.freeze({id:"top",label:"Top",direction:[0,1,.001],printedPage:null}),
 Object.freeze({id:"print-fork",label:"Print fork",direction:[1,.15,.27],printedPage:14}),
 Object.freeze({id:"print-hub",label:"Print hub",direction:[.63,-.45,.65],printedPage:15}),
]);
export function cameraViewDirection(name){
 if(typeof name!=="string")throw Error("unknown source camera study");
 const item=CAMERA_VIEW_PRESETS.find(x=>x.id===name);
 if(!item)throw Error("unknown source camera study");
 const [x,y,z]=item.direction;
 const norm=Math.hypot(x,y,z);
 if(!Number.isFinite(norm)||norm<=0)throw Error("invalid experimental camera");
 return Object.freeze({
  vector:Object.freeze([x/norm,y/norm,z/norm]),
  printedPage:item.printedPage,
  label:item.label,
  camera_is_original_1994_rendering:false,
  model_mesh_geometry_unchanged:true,
 });
}
