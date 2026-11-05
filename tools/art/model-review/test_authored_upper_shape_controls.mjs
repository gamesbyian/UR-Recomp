import test from 'node:test';
import assert from 'node:assert/strict';
import {SOURCE_STEM,SOURCE_STEM_LENGTH,SADDLE_HEIGHT,SHAPE_MODES,sourceShapeIntervention} from './authored_upper_shape_controls.mjs';

test('five fixed source-authored upper-model visual preview hypotheses',()=>{
 assert.deepEqual(SHAPE_MODES,['original','saddle-up','saddle-down','frame-short','frame-long']);
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
 for(const invalid of [null,undefined,{},true,'fake','0.12']){
  assert.throws(()=>sourceShapeIntervention(invalid),/unknown/);
 }
});
