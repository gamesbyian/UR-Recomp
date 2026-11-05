import test from 'node:test';
import assert from 'node:assert/strict';
import {SOURCE_STEM,SOURCE_STEM_LENGTH,SADDLE_HEIGHT,SHAPE_MODES,sourceShapeIntervention,saddleCupZ} from './authored_upper_shape_controls.mjs';

test('five fixed source-authored upper-model visual preview hypotheses',()=>{
 assert.deepEqual(SHAPE_MODES,['original','saddle-up','saddle-down','frame-short','frame-long','saddle-narrow','saddle-wide','saddle-cup-deep','saddle-cup-soft']);
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
