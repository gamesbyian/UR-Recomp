// Source-owned 2026 foot-platform kinematics, NOT recovered 1994 motion.
// Crank rods rotate; the two platforms and treads translate on opposing
// circular orbits but stay level, unlike the old rigid-parent viewer scrub.
import {PEDAL_PHASE,sourceCrankDegrees,sourcePhaseDelta,SOURCE_SHA} from './direct_drive_hypothesis.mjs';
const RADIUS=.31, Y_EXCLUSION=.10;
export function verifySeparatedFootpadGeometry(geometry){
 if(!geometry?.getAttribute || !geometry?.getIndex)throw Error('missing source footpad geometry');
 const pos=geometry.getAttribute('position'),norm=geometry.getAttribute('normal'),idx=geometry.getIndex();
 if(!pos||!norm||pos.itemSize!==3||norm.itemSize!==3||norm.count!==pos.count||
    pos.count===0||!idx||idx.count%3)throw Error('incomplete indexed footpad surface');
 const sideCounts=[0,0];
 for(let i=0;i<pos.count;i++){
  const numbers=[pos.getX(i),pos.getY(i),pos.getZ(i),norm.getX(i),norm.getY(i),norm.getZ(i)];
  if(!numbers.every(Number.isFinite)||Math.abs(pos.getY(i))<=Y_EXCLUSION)
   throw Error('nonfinite or axle-crossing footpad vertex');
 }
 for(let i=0;i<idx.count;i+=3){
  const vertices=[idx.getX(i),idx.getX(i+1),idx.getX(i+2)];
  if(vertices.some(v=>!Number.isInteger(v)||v<0||v>=pos.count))
   throw Error('footpad face index out of bounds');
  const sign=Math.sign(pos.getY(vertices[0]));
  if(vertices.some(v=>Math.sign(pos.getY(v))!==sign))
   throw Error('footpad triangle crosses crank centreplane');
  sideCounts[sign===1?0:1]++;
 }
 if(!sideCounts[0]||sideCounts[0]!==sideCounts[1])
  throw Error('opposed footpad face topology differs');
 return {positiveFaces:sideCounts[0],negativeFaces:sideCounts[1],vertices:pos.count};
}
export function levelFootpadGeometry(source,target,pose,sha,step){
 if(sha!==SOURCE_SHA||!Object.hasOwn(PEDAL_PHASE,pose))
  throw Error('source-qualified 2026 pedal pose required');
 sourcePhaseDelta(pose,sha);
 const degrees=sourceCrankDegrees(step);
 if(source===target)throw Error('source GLB buffer cannot be mutated');
 const proof=verifySeparatedFootpadGeometry(source);
 const old=source.getAttribute('position'),out=target.getAttribute('position');
 const oldN=source.getAttribute('normal'),outN=target.getAttribute('normal');
 if(!out||!outN||out.count!==old.count||outN.count!==oldN.count)
  throw Error('temporary geometry layout differs from source');
 const phase=PEDAL_PHASE[pose]*Math.PI/180,angle=(degrees%360)*Math.PI/180;
 const c=Math.cos(angle),s=Math.sin(angle);
 for(let i=0;i<old.count;i++){
  const side=Math.sign(old.getY(i));
  const anchorX=side*RADIUS*Math.cos(phase),anchorZ=side*RADIUS*Math.sin(phase);
  const dx=old.getX(i)-anchorX,dz=old.getZ(i)-anchorZ;
  // Parent Y(-delta) cancels this Y(+delta). Translation of the spindle
  // survives, while the surface orientation stays axis-aligned in world.
  out.setXYZ(i,anchorX+c*dx+s*dz,old.getY(i),anchorZ-s*dx+c*dz);
  const nx=oldN.getX(i),nz=oldN.getZ(i);
  outN.setXYZ(i,c*nx+s*nz,oldN.getY(i),-s*nx+c*nz);
 }
 out.needsUpdate=true;outN.needsUpdate=true;
 target.computeBoundingSphere?.();target.computeBoundingBox?.();
 return {...proof,phaseDegrees:PEDAL_PHASE[pose],crankDeltaDegrees:degrees,
         platformWorldOrientationDegrees:0,opposedOrbits:true,
         sourceGeometryUnchanged:true,original1994KinematicsRecovered:false};
}
