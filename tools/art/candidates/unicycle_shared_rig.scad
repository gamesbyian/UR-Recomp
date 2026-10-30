// Uniracers experimental HD racer BLOCKOUT, 2026-10-18.
// One continuous 3D rig for every pose, not unrelated frame drawings.
// Owner's procedural-art visual veto remains fully effective. NOT shipping.
// Reference: original 1994 in-game title source at guest400, independently
// SHA-verified AOT artifact 11863045863 (ZIP 6fb7e9ad...), original gameplay.
// No original reference pixels/ROMs included or regenerated.
$fn=50;
rig_pose=is_undef(rig_pose)?"upright":rig_pose;
rig_color=is_undef(rig_color)?[0.11,0.35,0.87]:rig_color;
rig_time=is_undef(rig_time)?0:rig_time;
// Title-source proportions are provisional: variants are for comparative
// review ONLY, never a shipping default or a fitted 1994 3D model.
rig_saddle_span=is_undef(rig_saddle_span)?1:rig_saddle_span;
// A second bounded independent review axis: chunky pre-rendered fork mass.
// Default 1.0 preserves all original blockout pose semantics.
rig_frame_mass=is_undef(rig_frame_mass)?1:rig_frame_mass;
assert(rig_frame_mass >= 1 && rig_frame_mass <= 2,
       "out-of-scope unreviewed fork mass");
assert(rig_saddle_span >= 1 && rig_saddle_span <= 2.2,
       "out-of-scope unreviewed saddle shape");
function unit_time(t)=min(1,max(0,t));
function ease_time(t)=let(u=unit_time(t)) u*u*(3-2*u);
function vadd(a,b)=[a[0]+b[0],a[1]+b[1],a[2]+b[2]];
module member(a,b,r1,r2) {
  hull(){
    translate(a)sphere(r=r1,$fn=24);
    translate(b)sphere(r=r2,$fn=24);
  }
}
module torus(r,t) {
  rotate([90,0,0])rotate_extrude(convexity=6,$fn=80)
    translate([r,0,0])circle(r=t,$fn=22);
}
module tire() {
  color([0.075,0.083,0.09])torus(0.85,0.15);
  // Expose the light stripe on the near sidewall, not inside opaque rubber.
  translate([0,-0.15,0])color([0.14,0.16,0.16])torus(0.80,0.028);
}
module rim_and_hub() {
  color([0.68,0.76,0.81])torus(0.715,0.055);
  color([0.28,0.34,0.40])torus(0.63,0.022);
  for(i=[0:7]){
    a=i*45+11;
    color([0.72,0.80,0.85])
      member([0,-0.025,0],[0.705*sin(a),-0.025,0.705*cos(a)],0.042,0.019);
  }
  color([0.77,0.82,0.86])rotate([90,0,0])
    cylinder(h=0.36,r=0.15,center=true);
  color([0.32,0.37,0.43])rotate([90,0,0])
    cylinder(h=0.42,r=0.086,center=true);
}
module pedal_body(p) {
  translate(p)color([0.07,0.09,0.11])
    minkowski(){cube([0.39,0.17,0.115],center=true);sphere(r=0.036,$fn=16);}
  translate(vadd(p,[0,-0.124,0]))color([0.64,0.36,0.08])
    cube([0.25,0.012,0.064],center=true);
}
module pedals(phase=0) {
  p1=[0.31*cos(phase),0.39,0.31*sin(phase)];
  p2=[-0.31*cos(phase),-0.39,-0.31*sin(phase)];
  color([0.68,0.74,0.80])member([0,0.19,0],p1,0.055,0.036);
  color([0.68,0.74,0.80])member([0,-0.19,0],p2,0.055,0.036);
  pedal_body(p1);pedal_body(p2);
}
// A loft of consecutive cushion sections allows a cupped saddle.
// A single convex hull would flatten the original title character's valley.
module saddle_section(x,h,rx,ry,rz) {
  translate([x,0,h])scale([rx,ry,rz])sphere(1,$fn=40);
}
module saddle(lean=0) {
  translate([0.04,0,2.27])rotate([0,lean,0])scale([rig_saddle_span,1,1]){
    color([0.085,0.092,0.105])union(){
      hull(){
        saddle_section(-0.66,0.19,0.35,0.34,0.21);
        saddle_section(-0.16,-0.05,0.35,0.30,0.17);
      }
      hull(){
        saddle_section(-0.16,-0.05,0.35,0.30,0.17);
        saddle_section(0.43,0.06,0.35,0.28,0.16);
      }
      hull(){
        saddle_section(0.43,0.06,0.35,0.28,0.16);
        saddle_section(0.83,0.23,0.14,0.17,0.17);
      }
    }
    color([0.17,0.185,0.19])union(){
      hull(){
        saddle_section(-0.67,0.345,0.23,0.25,0.025);
        saddle_section(-0.23,0.105,0.20,0.20,0.018);
      }
      hull(){
        saddle_section(-0.23,0.105,0.20,0.20,0.018);
        saddle_section(0.43,0.207,0.21,0.175,0.018);
      }
    }
  }
}
module frame_member(a,b,r1,r2){
  member(a,b,r1*rig_frame_mass,r2*rig_frame_mass);
}
module fork_and_frame(){
  for(y=[-0.225,0.225]){
    color(rig_color)frame_member([-0.02,y,0.07],[-0.10,y,0.83],0.09,0.105);
    color(rig_color)frame_member([-0.10,y,0.83],[-0.17,y*0.63,1.42],0.105,0.14);
  }
  color(rig_color)frame_member([-0.17,0,1.39],[-0.25,0,2.09],0.16,0.126);
  color([0.75,0.81,0.84])frame_member([-0.21,0,1.91],[-0.19,0,2.13],0.116,0.105);
  color([0.30,0.40,0.45])frame_member([-0.20,0,2.1],[-0.03,0,2.2],0.10,0.09);
  color([0.52,0.60,0.67])rotate([90,0,0])cylinder(h=0.56,r=0.13,center=true);
}
module shared_rig(pedal=0,seat_lean=0){
  translate([0,0,1]){
    tire();rim_and_hub();fork_and_frame();pedals(pedal);saddle(seat_lean);
  }
}
// All stunt and motion poses are transforms of one coherent character mesh.
// Non-shipping animation probes. Continuous motion transforms a shared mesh.
// An in-air 360-degree spin pivots around character center, not wheel contact;
// any authentic original-frame stunt pivot remains to be measured.
module continuous_rig(time,spin=false){
  u=unit_time(time);
  pitch=spin?360*ease_time(u):0;
  translate([0,0,1.80]) rotate([0,-pitch,0]) translate([0,0,-1.80])
  rotate([3*sin(720*u),0,7*sin(360*u)])
    shared_rig(pedal=18+720*u,seat_lean=3*sin(360*u));
}
module rig(p){
  if(p=="upright")shared_rig(pedal=18,seat_lean=0);
  else if(p=="pedal")shared_rig(pedal=88,seat_lean=-5);
  else if(p=="wheelie")translate([0,0,0.16])rotate([0,-28,0])
    shared_rig(pedal=44,seat_lean=12);
  else if(p=="stunt")translate([0,0,1.80])rotate([0,-130,0])translate([0,0,-1.80])
    shared_rig(pedal=120,seat_lean=-9);
  else if(p=="bank")rotate([11,0,-8])
    shared_rig(pedal=150,seat_lean=4);
  else if(p=="ride")continuous_rig(rig_time,false);
  else if(p=="stunt_cycle")continuous_rig(rig_time,true);
  else assert(false,str("unknown rig_pose: ",p));
}
rig(rig_pose);
