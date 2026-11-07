import assert from 'node:assert/strict';
import {verifySeparatedFootpadGeometry,levelFootpadGeometry} from './pedal_level_motion.mjs';
import {PEDAL_PHASE,SOURCE_SHA,sourceCrankDegrees} from './direct_drive_hypothesis.mjs';
class Attribute{
 constructor(a,size=3){this.a=Float64Array.from(a);this.itemSize=size;this.count=this.a.length/size;}
 getX(i){return this.a[i*this.itemSize]}
 getY(i){return this.a[i*this.itemSize+1]}
 getZ(i){return this.a[i*this.itemSize+2]}
 setXYZ(i,x,y,z){this.a.set([x,y,z],i*this.itemSize)}
 clone(){return new Attribute(this.a,this.itemSize)}
}
class Geometry{
 constructor(v,f,n){this.p=new Attribute(v);this.f=new Attribute(f,1);this.n=new Attribute(n);}
 getAttribute(k){return k==='position'?this.p:k==='normal'?this.n:null}
 getIndex(){return this.f}
 clone(){const g=new Geometry([],[],[]);g.p=this.p.clone();g.n=this.n.clone();g.f=this.f.clone();return g}
 computeBoundingSphere(){}
 computeBoundingBox(){}
}
function sample(pose){
 const phase=PEDAL_PHASE[pose]*Math.PI/180,v=[],n=[],f=[];
 for(const side of [1,-1]){
  const px=side*.31*Math.cos(phase),pz=side*.31*Math.sin(phase),py=side*.39;
  const start=v.length/3;
  for(const [dx,dz] of [[-.1,-.03],[.1,-.03],[.1,.03],[-.1,.03]]){
   v.push(px+dx,py,pz+dz);n.push(0,0,1);
  }
  f.push(start,start+1,start+2,start,start+2,start+3);
 }
 return new Geometry(v,f,n);
}
function near(a,b){assert.ok(Math.abs(a-b)<1e-9,String(a)+' != '+String(b))}
for(const pose of Object.keys(PEDAL_PHASE)){
 const source=sample(pose),raw=source.p.a.slice(),rawNormals=source.n.a.slice();
 assert.deepEqual(verifySeparatedFootpadGeometry(source),
                  {positiveFaces:2,negativeFaces:2,vertices:8});
 for(const step of [0,1,2,4,8,16,24,32,47,63,64]){
  const candidate=source.clone(),proof=levelFootpadGeometry(source,candidate,pose,SOURCE_SHA,step);
  assert.equal(proof.crankDeltaDegrees,sourceCrankDegrees(step));
  assert.equal(proof.sourceGeometryUnchanged,true);
  const d=sourceCrankDegrees(step)*Math.PI/180,c=Math.cos(d),s=Math.sin(d);
  for(let i=0;i<8;i++){
   const side=i<4?1:-1,phase=PEDAL_PHASE[pose]*Math.PI/180;
   const ax=side*.31*Math.cos(phase),az=side*.31*Math.sin(phase);
   const x=c*candidate.p.getX(i)-s*candidate.p.getZ(i);
   const z=s*candidate.p.getX(i)+c*candidate.p.getZ(i);
   near(x,c*ax-s*az+(raw[i*3]-ax));
   near(z,s*ax+c*az+(raw[i*3+2]-az));
   const nx=c*candidate.n.getX(i)-s*candidate.n.getZ(i);
   const nz=s*candidate.n.getX(i)+c*candidate.n.getZ(i);
   near(nx,source.n.getX(i));near(nz,source.n.getZ(i));
  }
  assert.deepEqual(source.p.a,raw);assert.deepEqual(source.n.a,rawNormals);
 }
}
for(const step of [-1,65,.5,NaN,Infinity])
 assert.throws(()=>levelFootpadGeometry(sample('upright'),sample('upright').clone(),'upright',SOURCE_SHA,step));
const sameGeometry=sample('upright');
assert.throws(()=>levelFootpadGeometry(sameGeometry,sameGeometry,'upright',SOURCE_SHA,1),/source GLB buffer/);
assert.throws(()=>levelFootpadGeometry(sample('upright'),sample('upright').clone(),'upright','untrusted',1));
assert.throws(()=>levelFootpadGeometry(sample('upright'),sample('upright').clone(),'no-pose',SOURCE_SHA,1));
const bad=sample('upright');bad.p.setXYZ(0,0,0,0);
assert.throws(()=>verifySeparatedFootpadGeometry(bad),/axle-crossing/);
const crossing=sample('upright');crossing.f.a[0]=4;
assert.throws(()=>verifySeparatedFootpadGeometry(crossing),/crosses crank centreplane/);
console.log('PASS original 2026 footpad geometry: 5 poses, 11 steps, both sides, normals, resets and unsafe-input guards');
