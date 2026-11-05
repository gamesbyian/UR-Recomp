// Source-authored 2026 GLB *inspection* controls, not original 1994 animation.
// Exactly one independent saddle mounting translation OR one frame z scale.
export const SOURCE_STEM=[.29,0,.88];
export const SOURCE_STEM_LENGTH=Math.hypot(...SOURCE_STEM);
export const SADDLE_HEIGHT=2.27;
export const SHAPE_MODES=Object.freeze(['original','saddle-up','saddle-down','frame-short','frame-long','saddle-narrow','saddle-wide','saddle-cup-deep','saddle-cup-soft','fork-crown-narrow','fork-crown-full']);
export function sourceShapeIntervention(mode){
 if(!SHAPE_MODES.includes(mode)||typeof mode!=='string')throw Error('unknown experimental 2026 upper-model hypothesis');
 let stroke=0,stretch=1,saddleSpan=1,saddleCup=0,crownScale=1;
 if(mode==='saddle-up')stroke=.12;
 if(mode==='saddle-down')stroke=-.12;
 if(mode==='frame-short')stretch=.96;
 if(mode==='frame-long')stretch=1.04;
 if(mode==='saddle-narrow')saddleSpan=.9;
 if(mode==='saddle-wide')saddleSpan=1.1;
 if(mode==='saddle-cup-deep')saddleCup=-.08;
 if(mode==='saddle-cup-soft')saddleCup=.08;
 if(mode==='fork-crown-narrow')crownScale=.9;
 if(mode==='fork-crown-full')crownScale=1.1;
 const offset=[
  SOURCE_STEM[0]/SOURCE_STEM_LENGTH*stroke,
  0,
  SOURCE_STEM[2]/SOURCE_STEM_LENGTH*stroke + SADDLE_HEIGHT*(stretch-1)
 ];
 if(!offset.every(Number.isFinite))throw Error('nonfinite authored upper model offset');
 return Object.freeze({mode,stroke,stretch,saddleSpan,saddleCup,crownScale,offset:Object.freeze(offset)});
}

/** The exact predeclared 2026 center-cup deform used by experimental Python.
 * Shared X/Z limits for BOTH saddle material meshes keep coincident vertices
 * together; the X tips and lower 20% of saddle Z remain unchanged.
 */
export function saddleCupZ(x,z,cup,bounds){
 if(typeof cup!=='number'||![ -.08,.08 ].includes(cup)||
    typeof x!=='number'||typeof z!=='number'||
    !Number.isFinite(x)||!Number.isFinite(z)||
    !Array.isArray(bounds)||bounds.length!==4||
    !bounds.every(v=>typeof v==='number'&&Number.isFinite(v)))
  throw Error('finite original saddle geometry and frozen cup offset required');
 const [xmin,xmax,zmin,zmax]=bounds;
 if(xmax-xmin<=1e-9||zmax-zmin<=1e-9||
    x<xmin-1e-8||x>xmax+1e-8||z<zmin-1e-8||z>zmax+1e-8)
  throw Error('invalid source-authored saddle bounds');
 const xcenter=(xmin+xmax)/2,xradius=(xmax-xmin)/2;
 const nx=Math.max(-1,Math.min(1,(x-xcenter)/xradius));
 const wx=(1-nx*nx)**2;
 const zn=(z-zmin)/(zmax-zmin);
 const u=Math.max(0,Math.min(1,(zn-.2)/.8));
 return z+cup*wx*(u*u*(3-2*u));
}


// Authored 2026 SCAD fork centrelines, original source-mesh LOCAL coordinates.
// These values do NOT imply the original 1994 production mesh/camera.
export function forkCrownXYZ(x,y,z,scale){
 if(![.9,1.1].includes(scale)||
    ![x,y,z].every(v=>typeof v==='number'&&Number.isFinite(v)))
   throw Error('frozen source-model crown radius and finite original xyz required');
 const stemX=(z<=1.39?
  -.10+(z-.83)*(-.17+.10)/(1.39-.83):
  -.17+(z-1.39)*(-.25+.17)/(2.09-1.39));
 const phase=Math.abs((z-1.42)/.56);
 const weight=phase<1?(1-phase*phase)**2:0;
 const radius=1+(scale-1)*weight;
 return [stemX+(x-stemX)*radius,y*radius,z];
}
