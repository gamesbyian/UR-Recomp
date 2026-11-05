#!/usr/bin/env python3
"""Check real original 24-tick saddle-only 2026 rig against both racer sprites.

Original-source chronological and distinct 2D alpha groups are scored
separately. No inferred 1994 3D geometry, physical joint degrees or owner art.
"""
from __future__ import annotations
import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import runpy

from tools.art.score_original_mesen24_fixed_pivot_glb import (
    check_receipts,read_original_roles,source_center,anchor,registered_mask4,
    rotate_source_2d,metric,fixed_source_y_band_metrics,SOURCE_Y_BANDS,sha,CAMERA_SHA,SCAD_SHA,
)
from tools.art.experimental_fixed_root_orbit import apply_root_scene
from tools.art.experimental_temporary_saddle_lean import temporary_saddle_pitch
from tools.art.experimental_world_level_saddle import temporary_saddle_world_attitude
from tools.art.experimental_saddle_stem_slide import temporary_saddle_stem_slide
from tools.art.experimental_upper_frame_stretch import temporary_upper_frame_stretch
from tools.art.experimental_saddle_span import temporary_saddle_span
from tools.art.experimental_saddle_cup import temporary_saddle_cup
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-ORIGINAL-24TICK-REAL-2026-SADDLE-LEAN-GENERALIZATION/3"
TICKS=tuple(range(1601,1625))
SADDLE_TRIALS=(("axle_root_saddle_neutral",0.),
               ("axle_root_saddle_plus15",15.),
               ("axle_root_saddle_minus15",-15.))
# The first four controls retain the already executed, immutable 48-frame
# saddle-only baseline. Two further controls are predeclared 2026 hypotheses,
# never fitted independently for each source tick or player.
BASE_ARMS=("original_source_2d_rotation",)+tuple(x for x,_ in SADDLE_TRIALS)
DRIVE_TRIALS=(("axle_root_saddle_plus15_rom_phase_15deg","rom_phase"),
              ("axle_root_saddle_plus15_fixed_tick_24deg","fixed_tick"))
# Two further fixed, **identical mechanical** controls: the real saddle's
# mounting point continues following the 2026 root, but its world orientation
# is held at one immutable neutral-root +15deg reference. One intervention
# for each earlier source-phase/fixed-clock wheel control, both real players.
LEVEL_TRIALS=(("axle_root_saddle_world_level_rom_phase_15deg","rom_phase"),
              ("axle_root_saddle_world_level_fixed_tick_24deg","fixed_tick"))
MOTION_TRIALS=DRIVE_TRIALS+LEVEL_TRIALS
LEVEL_NAMES={name for name,_ in LEVEL_TRIALS}
# Independent saddle world-level *mount displacement* controls are globally
# predeclared, both signed directions and the same two old wheel drives.
SLIDE_TRIALS=(
    ("axle_root_saddle_slide_up012_rom_phase_15deg","rom_phase",.12),
    ("axle_root_saddle_slide_down012_rom_phase_15deg","rom_phase",-.12),
    ("axle_root_saddle_slide_up012_fixed_tick_24deg","fixed_tick",.12),
    ("axle_root_saddle_slide_down012_fixed_tick_24deg","fixed_tick",-.12),
)
SLIDE_SETTINGS={name:(mode,offset) for name,mode,offset in SLIDE_TRIALS}
ALL_MOTION_TRIALS=MOTION_TRIALS+tuple((name,mode) for name,mode,_ in SLIDE_TRIALS)
# A separate physical 2026 *mesh deformation*, not inferred original
# velocity. Only fork/frame axial vertices change, saddle follows its
# authored 2.27-unit mount; wheel/ground contact and all colours untouched.
STRETCH_TRIALS=(
    ("axle_root_upper_stretch096_rom_phase_15deg","rom_phase",.96),
    ("axle_root_upper_stretch104_rom_phase_15deg","rom_phase",1.04),
    ("axle_root_upper_stretch096_fixed_tick_24deg","fixed_tick",.96),
    ("axle_root_upper_stretch104_fixed_tick_24deg","fixed_tick",1.04),
)
STRETCH_SETTINGS={name:(mode,scale) for name,mode,scale in STRETCH_TRIALS}
FULL_MOTION_TRIALS=ALL_MOTION_TRIALS+tuple((name,mode) for name,mode,_ in STRETCH_TRIALS)
# Independent source-*mesh* width hypothesis. It does not move the saddle
# mounting pivot and does not infer the original 1994 production geometry.
SPAN_TRIALS=(
    ("axle_root_saddle_span090_rom_phase_15deg","rom_phase",.9),
    ("axle_root_saddle_span110_rom_phase_15deg","rom_phase",1.1),
    ("axle_root_saddle_span090_fixed_tick_24deg","fixed_tick",.9),
    ("axle_root_saddle_span110_fixed_tick_24deg","fixed_tick",1.1),
)
SPAN_SETTINGS={name:(mode,ratio) for name,mode,ratio in SPAN_TRIALS}
ALL_SHAPE_TRIALS=FULL_MOTION_TRIALS+tuple((name,mode) for name,mode,_ in SPAN_TRIALS)
# Unlike global saddle X-span, modify upper center contour only. The lower
# mount and outer tips remain fixed; BOTH source racers get identical controls.
CUP_TRIALS=(
    ("axle_root_saddle_cup_deep008_rom_phase_15deg","rom_phase",-.08),
    ("axle_root_saddle_cup_soft008_rom_phase_15deg","rom_phase",.08),
    ("axle_root_saddle_cup_deep008_fixed_tick_24deg","fixed_tick",-.08),
    ("axle_root_saddle_cup_soft008_fixed_tick_24deg","fixed_tick",.08),
)
CUP_SETTINGS={name:(mode,offset) for name,mode,offset in CUP_TRIALS}
ALL_CONTOUR_TRIALS=ALL_SHAPE_TRIALS+tuple((name,mode) for name,mode,_ in CUP_TRIALS)
ARMS=BASE_ARMS+tuple(name for name,_ in ALL_CONTOUR_TRIALS)


def drive_delta_degrees(phase:int,start_phase:int,tick:int,mode:str)->float:
    """Two fixed drive conventions, each with a zero delta at original tick1601.

    ROM phase is an exact 0..23 source *2D drawing* index. The 15-degree
    mapping is a counterfactual, not identified 1994 wheel/crank rotation.
    The 24-degree per-tick control is reused from the earlier bounded rig
    study and is not inferred from game physics.
    """
    if (type(phase) is not int or type(start_phase) is not int or
            type(tick) is not int or not 0<=phase<24 or
            not 0<=start_phase<24 or tick not in TICKS):
        raise ValueError("exact source ROM phase 0..23 and tick 1601..1624 required")
    if mode=="rom_phase":
        return float(((phase-start_phase)%24)*15)
    if mode=="fixed_tick":
        return float(((tick-1601)*24)%360)
    raise ValueError("only the two predeclared 2026 drive controls allowed")


def aggregate_original_timeline(rows:dict[int,dict],predictions:dict[int,dict[str,bytes]])->dict:
    """Keep temporal-frame and one-vote-per-unique-2D-source-shape distinct."""
    if (set(rows)!=set(TICKS) or set(predictions)!=set(TICKS) or
            any(set(predictions[t])!=set(ARMS) for t in TICKS)):
        raise ValueError("complete original 24-tick timeline and all candidate arms required")
    shapes={}
    for t in TICKS:
        original=rows[t]["alpha"]
        if type(original) is not bytes or len(original)!=4096 or set(original)-{0,1}:
            raise ValueError("original Mesen source alpha malformed")
        shapes.setdefault(sha(original),[]).append(t)
    outcome={}
    for arm in ARMS:
        scores={t:metric(rows[t]["alpha"],predictions[t][arm]) for t in TICKS}
        full={k:sum(score[k] for score in scores.values()) for k in ("tp","fp","fn")}
        unique_mean=[]
        for digest,times in shapes.items():
            unique_mean.append(sum(scores[t]["iou"] for t in times)/len(times))
        edge={}
        band_sums={name:{"tp":0,"fp":0,"fn":0} for name,_,_ in SOURCE_Y_BANDS}
        for previous,current in zip(TICKS[:-1],TICKS[1:]):
            source_edge=bytes(int(x!=y) for x,y in zip(
                rows[previous]["alpha"],rows[current]["alpha"]))
            candidate_edge=bytes(int(x!=y) for x,y in zip(
                predictions[previous][arm],predictions[current][arm]))
            edge[(previous,current)]=metric(source_edge,candidate_edge)
            for name,band in fixed_source_y_band_metrics(source_edge,candidate_edge).items():
                for count in ("tp","fp","fn"):
                    band_sums[name][count]+=band[count]
        sums={k:sum(v[k] for v in edge.values()) for k in ("tp","fp","fn")}
        if any(sum(band_sums[b][k] for b in band_sums)!=sums[k]
               for k in ("tp","fp","fn")):
            raise ValueError("temporal source band census disagrees with full edge score")
        band_report={}
        for name,y0,y1 in SOURCE_Y_BANDS:
            counts=band_sums[name]
            denom=sum(counts.values())
            band_report[name]={
                "source_image_y_inclusive":[y0,y1],
                "source_chronological_edge_count":len(edge),
                "source_actual_xor_changed_pixel_instances":counts["tp"]+counts["fn"],
                "2026_candidate_xor_changed_pixel_instances":counts["tp"]+counts["fp"],
                "tp_fp_fn":counts,
                "pooled_temporal_alpha_change_iou":
                    round(counts["tp"]/denom,8) if denom else 1.,
            }
        outcome[arm]={
            "original_chronological_source_frame_count":len(TICKS),
            "original_unique_64px_binary_shape_count":len(shapes),
            "source_frame_pooled_alpha_iou":round(full["tp"]/sum(full.values()),8),
            "source_unique_shape_equal_vote_mean_alpha_iou":
                round(sum(unique_mean)/len(unique_mean),8),
            "source_actual_timeline_edge_count":len(edge),
            "source_actual_23_consecutive_edge_change_tp_fp_fn":sums,
            "source_actual_23_consecutive_edge_change_fixed_y_bands":band_report,
            "source_actual_23_consecutive_edge_change_pooled_iou":
                round(sums["tp"]/sum(sums.values()),8)
                if sum(sums.values()) else 1.,
            "source_actual_23_consecutive_edge_change_mean_iou":
                round(sum(v["iou"] for v in edge.values())/len(edge),8),
            "source_chronological_full_alpha_tp_fp_fn":full,
            "per_original_chronological_edge":[
                {"source_ticks":[a,b],**edge[(a,b)]}
                for a,b in zip(TICKS[:-1],TICKS[1:])],
        }
    return {
        "original_unique_binary_source_alpha_shape_sha256_to_ticks":{
            key:values for key,values in sorted(shapes.items())},
        "arms":outcome,
    }


def analyze(zip_raw:bytes,pose_raw:bytes,axis_raw:bytes,
            camera_raw:bytes,verified_exports:Path)->dict:
    import numpy as np
    import trimesh
    from tools.art.render_racer_glb_projection import render_mask
    from tools.art.count_real_glb_parent_source_y_bands import project_real_parent_masks256
    from tools.art.partition_2026_glb_parent_edge import source_vs_model_motion_regions
    pose,axis,camera=check_receipts(zip_raw,pose_raw,axis_raw,camera_raw)
    if sha(camera_raw)!=CAMERA_SHA:
        raise ValueError("previous frozen original source camera SHA changed")
    originals=read_original_roles(zip_raw,pose,all_original_ticks=True)
    if any(set(rows)!=set(TICKS) for rows in originals.values()):
        raise ValueError("missing authentic 24 original PPU source snapshots")

    validate=runpy.run_path(str(Path(__file__).resolve().parent /
                               "model-review/stage_pages.py"))["validate"]
    pointer,outputs=validate(verified_exports,"upright")
    source=outputs["glb"].read_bytes()
    if (pointer["source_sha256"]!=SCAD_SHA or
            pointer["glb_sha256"]!=hashlib.sha256(source).hexdigest() or
            source[:4]!=b"glTF"):
        raise ValueError("same source-owned 2026 GLB success receipt changed")
    scene=trimesh.load(outputs["glb"],file_type="glb",force="scene",process=False)

    def model4(angle:int,lean:float,wheel:float=0.,saddle_level:bool=False,
               saddle_stroke:float=0.,upper_stretch:float=0.,
               saddle_span:float=0.,saddle_cup:float=0.):
        apply_root_scene(scene,angle,"wheel_axle",wheel,0.)
        with temporary_saddle_pitch(scene,lean):
            adjustment=(temporary_saddle_world_attitude(scene,level_reference)
                        if saddle_level else nullcontext())
            with adjustment:
                displacement=(temporary_saddle_stem_slide(scene,saddle_stroke)
                              if saddle_stroke else nullcontext())
                with displacement:
                    deformation=(temporary_upper_frame_stretch(scene,upper_stretch)
                                 if upper_stretch else nullcontext())
                    with deformation:
                        span=(temporary_saddle_span(scene,saddle_span)
                              if saddle_span else nullcontext())
                        with span:
                            contour=(temporary_saddle_cup(scene,saddle_cup)
                                     if saddle_cup else nullcontext())
                            with contour:
                                world=(scene.to_geometry() if callable(
                                    getattr(scene,"to_geometry",None)) else scene.dump(concatenate=True))
                                result=render_mask(np.asarray(world.vertices),
                                                   np.asarray(world.faces),camera)
        return result.astype(bool)

    neutral=model4(0,0.)
    # One authored 2026 rest orientation, not any original 1994 fitted
    # source frame. Mount world positions still move with the root.
    apply_root_scene(scene,0,"wheel_axle",0.,0.)
    with temporary_saddle_pitch(scene,15.):
        level_reference=np.asarray(scene.graph.get("saddle")[0][:3,:3]).copy()
    neutral_anchor=anchor(bytes(neutral[2::4,2::4].astype(np.uint8).ravel()))
    center=source_center(axis)
    if (center[0],center[1])!=(31.515625,19.578125):
        raise ValueError("the exact original even-only source 2D calibration changed")
    renders={}
    data={}
    for role,actual in originals.items():
        reference=actual[1601]
        original_anchor=anchor(reference["alpha"])
        predictions={}
        samples={}
        for t in TICKS:
            frame=actual[t]
            source_mask=frame["alpha"]
            arms={
                "original_source_2d_rotation":rotate_source_2d(
                    reference["alpha"],frame["angle"]-reference["angle"],center)
            }
            for name,lean in SADDLE_TRIALS:
                key=(frame["angle"],lean,0.)
                if key not in renders:
                    renders[key]=model4(frame["angle"],lean,0.)
                arms[name]=registered_mask4(renders[key],original_anchor,neutral_anchor)
            for name,mode in ALL_CONTOUR_TRIALS:
                wheel=drive_delta_degrees(frame["phase"],reference["phase"],t,mode)
                stroke=SLIDE_SETTINGS[name][1] if name in SLIDE_SETTINGS else 0.
                stretch=STRETCH_SETTINGS[name][1] if name in STRETCH_SETTINGS else 0.
                span=SPAN_SETTINGS[name][1] if name in SPAN_SETTINGS else 0.
                cup=CUP_SETTINGS[name][1] if name in CUP_SETTINGS else 0.
                is_level=name in LEVEL_NAMES or name in SLIDE_SETTINGS or name in STRETCH_SETTINGS or name in SPAN_SETTINGS or name in CUP_SETTINGS
                key=(frame["angle"],15.,wheel,"world_level","cup",cup) if cup else (
                    (frame["angle"],15.,wheel,"world_level","span",span) if span else (
                    (frame["angle"],15.,wheel,"world_level","stretch",stretch) if stretch else (
                    (frame["angle"],15.,wheel,"world_level",stroke) if stroke else (
                    (frame["angle"],15.,wheel,"world_level") if is_level else
                    (frame["angle"],15.,wheel)))))
                if key not in renders:
                    renders[key]=model4(frame["angle"],15.,wheel,is_level,stroke,stretch,span,cup)
                arms[name]=registered_mask4(renders[key],original_anchor,neutral_anchor)
            if set(arms)!=set(ARMS):
                raise ValueError("incomplete original 24-tick 2D/3D model controls")
            predictions[t]=arms
            samples[str(t)]={
                "source_true_original_Mesen_tick":t,
                "source_original_ROM_phase_index":frame["phase"],
                "source_original_ROM_orientation_index":frame["angle"],
                "source_opaque_64px_pixels":sum(source_mask),
                "source_2D_alpha_sha256":sha(source_mask),
                "source_actual_and_candidate_full_alpha":{
                    name:metric(source_mask,img) for name,img in arms.items()},
                "source_actual_and_candidate_fixed_y_bands":{
                    name:fixed_source_y_band_metrics(source_mask,img)
                    for name,img in arms.items()},
            }
        timeline=aggregate_original_timeline(actual,predictions)
        data[role]={
            "one_source_tick1601_lower_alpha_anchor_x2y2":list(original_anchor),
            "original_24_tick_samples":samples,
            **timeline,
        }
    # Predeclared genuine source upper-change events, not a shape or fit
    # selected from current model predictions. Compare the two existing
    # globally fixed source-phase/fixed-tick drives using real named 2026
    # parent meshes and the *same* actual GLB/camera/first-tick anchor.
    selected_upper_source_events={"blue":(1602,1603),"red":(1605,1606)}
    if set(originals)!=set(selected_upper_source_events):
        raise ValueError("authentic source upper events require both original racers")
    original_vs_authored_2026_parent_motion={}
    for role,(first,last) in selected_upper_source_events.items():
        original=originals[role]
        placement=anchor(original[1601]["alpha"])
        events={}
        for name,mode in ALL_CONTOUR_TRIALS:
            projected={}
            stroke=SLIDE_SETTINGS[name][1] if name in SLIDE_SETTINGS else 0.
            stretch=STRETCH_SETTINGS[name][1] if name in STRETCH_SETTINGS else 0.
            span=SPAN_SETTINGS[name][1] if name in SPAN_SETTINGS else 0.
            cup=CUP_SETTINGS[name][1] if name in CUP_SETTINGS else 0.
            is_level=name in LEVEL_NAMES or name in SLIDE_SETTINGS or name in STRETCH_SETTINGS or name in SPAN_SETTINGS or name in CUP_SETTINGS
            for tick in (first,last):
                frame=original[tick]
                wheel=drive_delta_degrees(frame["phase"],original[1601]["phase"],tick,mode)
                key=(frame["angle"],15.,wheel,"world_level","cup",cup) if cup else (
                    (frame["angle"],15.,wheel,"world_level","span",span) if span else (
                    (frame["angle"],15.,wheel,"world_level","stretch",stretch) if stretch else (
                    (frame["angle"],15.,wheel,"world_level",stroke) if stroke else (
                    (frame["angle"],15.,wheel,"world_level") if is_level else
                    (frame["angle"],15.,wheel)))))
                if key not in renders:
                    raise ValueError("same already rendered actual GLB pose missing")
                apply_root_scene(scene,frame["angle"],"wheel_axle",wheel,0.)
                with temporary_saddle_pitch(scene,15.):
                    adjustment=(temporary_saddle_world_attitude(scene,level_reference)
                                if is_level else nullcontext())
                    with adjustment:
                        displacement=(temporary_saddle_stem_slide(scene,stroke)
                                      if stroke else nullcontext())
                        with displacement:
                            deformation=(temporary_upper_frame_stretch(scene,stretch)
                                         if stretch else nullcontext())
                            with deformation:
                                dimension=(temporary_saddle_span(scene,span)
                                           if span else nullcontext())
                                with dimension:
                                    contour=(temporary_saddle_cup(scene,cup)
                                             if cup else nullcontext())
                                    with contour:
                                        parent256=project_real_parent_masks256(scene,camera)
                union=np.logical_or.reduce(list(parent256.values()))
                if not np.array_equal(union,renders[key]):
                    raise ValueError("authored 2026 GLB parents do not reproduce whole")
                parent64={part:registered_mask4(mask,placement,neutral_anchor)
                          for part,mask in parent256.items()}
                if bytes(int(any(part[k] for part in parent64.values()))
                         for k in range(4096))!=registered_mask4(union,placement,neutral_anchor):
                    raise ValueError("registered actual 2026 GLB parent union not conserved")
                projected[tick]=parent64
            outcome=source_vs_model_motion_regions(
                original[first]["alpha"],original[last]["alpha"],
                projected[first],projected[last])
            whole_edge=[row for row in data[role]["arms"][name][
                "per_original_chronological_edge"]
                if row["source_ticks"]==[first,last]]
            if len(whole_edge)!=1 or any(outcome["source_vs_2026_motion_tp_fp_fn"][k]!=
                                         whole_edge[0][k] for k in ("tp","fp","fn")):
                raise ValueError("model parent edge disagrees with previously qualified whole GLB")
            events[name]=outcome
        original_vs_authored_2026_parent_motion[role]={
            "source_original_consecutive_Mesen_ticks":[first,last],
            "retrospectively_inspected_original_source_event":True,
            "2026_candidate_motion_controls":events,
        }
    return {
        "schema":SCHEMA,
        "source_exact_original_USA_ROM_sha256":pose["original_usa_ROM_sha256"],
        "source_exact_original_Mesen24_archive_sha256":sha(zip_raw),
        "source_exact_ROM_phase_orientation_report_sha256":sha(pose_raw),
        "source_exact_64_angle_report_sha256":sha(axis_raw),
        "source_unchanged_7_6_camera_sha256":sha(camera_raw),
        "current_source_authored_2026_SCAD_sha256":SCAD_SHA,
        "current_successful_2026_16_material_GLB_sha256":pointer["glb_sha256"],
        "source_original_timeline_ticks":[1601,1624],
        "source_each_player_has_all_24_consecutive_original_PPU_images":True,
        "source_orientation_to_root_angle_is_uncalibrated_2026_hypothesis":True,
        "2026_saddle_only_constant_degrees_both_players_all_ticks":[0.,15.,-15.],
        "2026_additional_drive_controls_predeclared_not_fitted":list(DRIVE_TRIALS),
        "2026_saddle_world_level_controls_predeclared_not_fitted":list(LEVEL_TRIALS),
        "2026_independent_saddle_stem_displacement_controls":list(SLIDE_TRIALS),
        "2026_signed_stem_offsets_are_authoring_units_not_original_1994_stroke":True,
        "2026_upper_frame_stretch_controls_predeclared_not_fitted":list(STRETCH_TRIALS),
        "2026_upper_frame_stretch_is_not_original_velocity_law":True,
        "2026_authored_saddle_longitudinal_span_controls":list(SPAN_TRIALS),
        "2026_authored_upper_cupped_saddle_contour_controls":list(CUP_TRIALS),
        "2026_saddle_cup_is_not_recovered_original_1994_surface":True,
        "2026_saddle_shape_magnitude_not_original_1994_geometry":True,
        "2026_world_level_saddle_retains_real_moving_mount_position":True,
        "2026_saddle_world_attitude_reference_is_authored_rest_not_original":True,
        "source_ROM_phase_24_to_2026_wheel_degrees_is_uncalibrated":True,
        "source_2026_fixed_24deg_per_tick_is_not_original_animation_cadence":True,
        "source_phase_drive_is_relative_to_own_player_original_tick1601":True,
        "2026_frame_fork_wheel_geometry_camera_and_mount_unchanged":True,
        "source_unique_binary_silhouettes_grouped_without_duplicate_vote_weight":True,
        "source_actual_timeline_motion_distinct_from_repeated_static_shapes":True,
        "original_source_fixed_y_band_temporal_edges_partition_exactly":True,
        "original_source_fixed_y_bands_are_not_authentic_1994_part_labels":True,
        "source_viewpoint_families_are_known_NOT_prospective_blind":True,
        "original_1994_3D_mesh_camera_joint_or_source_materials_recovered":False,
        "owner_2026_character_art_likeness_approved":False,
        "real_2026_GLb_unique_model_pose_renders_cached":len(renders),
        "original_source_per_role":data,
        "original_upper_event_2026_visible_parent_motion":
            original_vs_authored_2026_parent_motion,
        "2026_visible_motion_ambiguous_parent_overlap_reported_separately":True,
        "source_y_image_bands_not_1994_anatomical_part_labels":True,
    }


def summary_for_exact_original_source(record:dict)->dict:
    """Read-only original 48-frame results independent of variable GLB bytes."""
    if (not isinstance(record,dict) or record.get("schema")!=SCHEMA or
            set(record.get("original_source_per_role",{}))!={"blue","red"}):
        raise ValueError("complete real original Mesen source/model report required")
    result={}
    for role,entry in record["original_source_per_role"].items():
        if (not set(BASE_ARMS).issubset(set(entry.get("arms",{}))) or
                set(entry.get("original_24_tick_samples",{}))!={str(t) for t in TICKS}):
            raise ValueError("all 24 authentic original ticks and candidate arms required")
        result[role]={}
        for arm in BASE_ARMS:
            arm_row=entry["arms"][arm]
            if (arm_row.get("original_chronological_source_frame_count")!=24 or
                    arm_row.get("source_actual_timeline_edge_count")!=23):
                raise ValueError("genuine source 24-frame/23-edge chronology required")
            result[role][arm]={
                "unique_shapes":arm_row["original_unique_64px_binary_shape_count"],
                "chronological_pooled_iou":arm_row["source_frame_pooled_alpha_iou"],
                "unique_shape_equal_vote_mean_iou":
                    arm_row["source_unique_shape_equal_vote_mean_alpha_iou"],
                "real_23_tick_edge_change_pooled_iou":
                    arm_row["source_actual_23_consecutive_edge_change_pooled_iou"],
            }
    return result


def check_exact_source_evidence(record:dict,evidence:dict)->None:
    """Detect drift from one actual original ROM and authored-GLB run.

    The GLB file SHA may vary, but source OpenSCAD SHA and exact exporter
    receipt must remain verified by analyze() before calling this helper.
    """
    if (not isinstance(evidence,dict) or
            evidence.get("schema")!="UR-ART4K-EXACT-ORIGINAL-MESEN24-SADDLE-TEMPORAL-EVIDENCE/1"):
        raise ValueError("wrong original Mesen24 saddle temporal evidence schema")
    source=evidence.get("producer",{})
    checks={
        "original_Mesen24_archive_sha256":record.get("source_exact_original_Mesen24_archive_sha256"),
        "original_pose_report_sha256":record.get("source_exact_ROM_phase_orientation_report_sha256"),
        "original_axis_sha256":record.get("source_exact_64_angle_report_sha256"),
        "provisional_camera_sha256":record.get("source_unchanged_7_6_camera_sha256"),
        "current_2026_authored_SCAD_sha256":record.get("current_source_authored_2026_SCAD_sha256"),
    }
    if any(source.get(key)!=value or type(value) is not str or len(value)!=64
           for key,value in checks.items()):
        raise ValueError("original source/2026 model provenance changed")
    if (source.get("original_1994_physical_3d_model_or_camera_recovered") is not False or
            source.get("original_art_likeness_approved") is not False or
            record.get("original_1994_3D_mesh_camera_joint_or_source_materials_recovered") is not False or
            record.get("owner_2026_character_art_likeness_approved") is not False):
        raise ValueError("original 3D/art likeness cannot be awarded by this experiment")
    if summary_for_exact_original_source(record)!=evidence.get("reported_per_role"):
        raise ValueError("actual original 48-frame saddle shape/motion scores drifted")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",required=True,type=Path)
    p.add_argument("--pose-report",required=True,type=Path)
    p.add_argument("--axis-report",required=True,type=Path)
    p.add_argument("--camera",required=True,type=Path)
    p.add_argument("--verified-exports",required=True,type=Path)
    p.add_argument("--expected-summary",type=Path,
                   help="SHA-bound prior executed original source/GLB baseline")
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=analyze(a.source_zip.read_bytes(),a.pose_report.read_bytes(),
                   a.axis_report.read_bytes(),a.camera.read_bytes(),a.verified_exports)
    if a.expected_summary is not None:
        check_exact_source_evidence(result,json.loads(a.expected_summary.read_text()))
    publish_text_once(a.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("OK ART4K_REAL_2026_SADDLE_ALL24_SOURCE_MOTION",
          json.dumps({role:{arm:{
                k:v for k,v in score.items() if k in (
                    "source_frame_pooled_alpha_iou",
                    "source_unique_shape_equal_vote_mean_alpha_iou",
                    "original_unique_64px_binary_shape_count",
                    "source_actual_23_consecutive_edge_change_pooled_iou")}
                    for arm,score in rec["arms"].items()}
                    for role,rec in result["original_source_per_role"].items()},
                     sort_keys=True))


if __name__=="__main__":
    main()
