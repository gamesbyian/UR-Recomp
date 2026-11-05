// Source-authored 2026 GLB *inspection* controls, not original 1994 animation.
// Exactly one independent saddle mounting translation OR one frame z scale.
export const SOURCE_STEM=[.29,0,.88];
export const SOURCE_STEM_LENGTH=Math.hypot(...SOURCE_STEM);
export const SADDLE_HEIGHT=2.27;
export const SHAPE_MODES=Object.freeze(['original','saddle-up','saddle-down','frame-short','frame-long']);
export function sourceShapeIntervention(mode){
 if(!SHAPE_MODES.includes(mode)||typeof mode!=='string')throw Error('unknown experimental 2026 upper-model hypothesis');
 let stroke=0,stretch=1;
 if(mode==='saddle-up')stroke=.12;
 if(mode==='saddle-down')stroke=-.12;
 if(mode==='frame-short')stretch=.96;
 if(mode==='frame-long')stretch=1.04;
 const offset=[
  SOURCE_STEM[0]/SOURCE_STEM_LENGTH*stroke,
  0,
  SOURCE_STEM[2]/SOURCE_STEM_LENGTH*stroke + SADDLE_HEIGHT*(stretch-1)
 ];
 if(!offset.every(Number.isFinite))throw Error('nonfinite authored upper model offset');
 return Object.freeze({mode,stroke,stretch,offset:Object.freeze(offset)});
}
