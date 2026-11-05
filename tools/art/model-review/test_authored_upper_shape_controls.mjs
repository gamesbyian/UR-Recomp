import test from 'node:test';
import assert from 'node:assert/strict';
import {SOURCE_STEM,SOURCE_STEM_LENGTH,SADDLE_HEIGHT,SHAPE_MODES,sourceShapeIntervention,saddleCupZ,forkCrownXYZ} from './authored_upper_shape_controls.mjs';

test('five fixed source-authored upper-model visual preview hypotheses',()=>{
 assert.deepEqual(SHAPE_MODES,['original','saddle-up','saddle-down','frame-short','frame-long','saddle-narrow','saddle-wide','saddle-cup-deep','saddle-cup-soft','fork-crown-narrow','fork-crown-full']);
 assert.deepEqual(sourceShapeIntervention('original').offset,[0,0,0]);
 assert.ok(Math.abs(Math.hypot(...SOURCE_STEM)/SOURCE_STEM_LENGTH-1)<1e-12);
 for(const [name,sign] of [['saddle-up',1],['saddle-down',-1]]){
  const p=sourceShapeIntervention(name);
  assert.equal(p.stroke,.12*sign);
  assert.equal(p.stretch,1);
  assert.ok(Math.abs(Math.hypot(...p.offset)-.12)<1e-12);
  assert.equal(p.offset[1],0);
 }
 for(const [name,scale] of [['frame-short',.96],['frame-long',1.04]]){
  const p=sourceShapeIntervention(name);
  assert.equal(p.stroke,0);
  assert.equal(p.stretch,scale);
  assert.equal(p.offset[0],0);
  assert.ok(Math.abs(p.offset[2]-SADDLE_HEIGHT*(scale-1))<1e-12);
 }
 for(const [name,factor] of [['saddle-narrow',.9],['saddle-wide',1.1]]){
  const p=sourceShapeIntervention(name);
  assert.equal(p.saddleSpan,factor);
  assert.equal(p.stroke,0);assert.equal(p.stretch,1);
  assert.deepEqual(p.offset,[0,0,0]);
 }
 for(const [mode,value] of [['saddle-cup-deep',-.08],['saddle-cup-soft',.08]]){
  const proposal=sourceShapeIntervention(mode);
  assert.equal(proposal.saddleCup,value);
  assert.equal(proposal.saddleSpan,1);
  assert.equal(proposal.stroke,0);
  assert.equal(proposal.stretch,1);
  assert.deepEqual(proposal.offset,[0,0,0]);
 }
 assert.equal(sourceShapeIntervention('original').saddleSpan,1);
 assert.equal(sourceShapeIntervention('original').saddleCup,0);
 assert.equal(sourceShapeIntervention('original').crownScale,1);
 for(const [mode,value] of [['fork-crown-narrow',.9],['fork-crown-full',1.1]]){
   const proposal=sourceShapeIntervention(mode);
   assert.equal(proposal.crownScale,value);
   assert.equal(proposal.stroke,0);assert.equal(proposal.stretch,1);
   assert.equal(proposal.saddleCup,0);assert.equal(proposal.saddleSpan,1);
   assert.deepEqual(proposal.offset,[0,0,0]);
 }
 for(const invalid of [null,undefined,{},true,'fake','0.12']){
  assert.throws(()=>sourceShapeIntervention(invalid),/unknown/);
 }
});

test('shared-bound saddle cupping leaves tips and lower mount fixed',()=>{
 const bounds=[-1,1,-.2,.6];
 for(const cup of [-.08,.08]){
  assert.equal(saddleCupZ(-1,.6,cup,bounds),.6);
  assert.equal(saddleCupZ(1,.6,cup,bounds),.6);
  assert.equal(saddleCupZ(0,-.2,cup,bounds),-.2);
  assert.equal(saddleCupZ(0,-.04,cup,bounds),-.04);
  assert.ok(Math.abs(saddleCupZ(0,.6,cup,bounds)-(.6+cup))<1e-12);
  assert.ok(Math.abs(saddleCupZ(.5,.6,cup,bounds)-
                     (.6+cup*(1-.25)**2))<1e-12);
  assert.equal(saddleCupZ(.13,.32,cup,bounds),saddleCupZ(.13,.32,cup,bounds));
 }
 for(const [cup,box] of [[0,bounds],[.09,bounds],[true,bounds],
      [-.08,null],[-.08,[1,1,0,1]],[-.08,[-1,1,0,0]]])
  assert.throws(()=>saddleCupZ(0,.3,cup,box));
 assert.throws(()=>saddleCupZ(2,.5,-.08,bounds));
 assert.throws(()=>saddleCupZ(0,NaN,-.08,bounds));
});

test('source-authored fork crown cross-section is localized and leaves axle + saddle unchanged',()=>{
 const cx=-.17+(1.42-1.39)*(-.25+.17)/(2.09-1.39);
 for(const scale of [.9,1.1]){
  const [x,y,z]=forkCrownXYZ(cx+.2,.1,1.42,scale);
  assert.ok(Math.abs(x-(cx+.2*scale))<1e-12);
  assert.ok(Math.abs(y-.1*scale)<1e-12);
  assert.equal(z,1.42);
  for(const original of [[-.2,.07,.86],[-.1,-.1,1.98],
                         [-.21,.08,2.09],[-.05,.1,.07]]){
   const result=forkCrownXYZ(...original,scale);
   for(let i=0;i<3;i++)
    assert.ok(Math.abs(result[i]-original[i])<1e-13,
              'boundary/source-mounted geometry changed');
  }
  const stationary=forkCrownXYZ(cx,0,1.42,scale);
  assert.ok(Math.abs(stationary[0]-cx)<1e-14);
  assert.equal(stationary[1],0);
 }
 for(const [factor,coords] of [[1,[0,0,1.42]],[true,[0,0,1.42]],
                               [.8,[0,0,1.42]],[1.1,[NaN,0,1.42]],
                               [.9,[0,Infinity,1.42]]])
  assert.throws(()=>forkCrownXYZ(...coords,factor));
});
