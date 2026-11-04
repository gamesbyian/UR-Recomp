#!/usr/bin/env python3
"""Bounded original 24-tick source silhouettes against one real five-parent GLB.

Reuses SHA-verified original Mesen PPU evidence, #3104 exact ROM pose IDs,
and the existing #2832 exporter attempt/receipt. No per-frame model fitting,
new geometry, camera adjustment or original 1994 3D interpretation.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import zipfile

ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
ZIP_SHA = "28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
POSE_SHA = "6286aedcda6080acf832ecece9fcdb879354db008e870bc00ada02db3ff3aa20"
AXIS_SHA = "23aa563c094471a3d7f1b5dcb12489cc1b5ca45b1240aee06fde3934a932bbd0"
CAMERA_SHA = "1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"
SCAD_SHA = "e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984"
SCHEMA = "UR-ART4K-ORIGINAL-MESEN24-FIXED-2026-ROOT-3D-VS-2D/1"
EVENTS = {"blue": ((1602,1603),(1609,1610)),
          "red": ((1605,1606),(1609,1610))}
SELECTED = {name:sorted({t for edge in edges for t in edge})
            for name,edges in EVENTS.items()}
ROLES = {"blue": (96,4), "red": (97,3)}
PIVOTS = ("wheel_axle", "historical_midbody")
# Fixed source-y diagnostic partitions, from the already-documented 1994
# upper event y4..14 / middle y15..26 / wheel-region y27..38.
# Include the entire 64px raster, with no semantic part assignment.
SOURCE_Y_BANDS = (("upper_y0_14",0,14),
                  ("middle_y15_26",15,26),
                  ("lower_y27_63",27,63))
ARM_NAMES = ("static_original_2d","source_original_2d_rotation",
             "static_2026_3d","wheel_axle_root_only",
             "historical_midbody_root_only",
             "wheel_axle_root_plus_phase","historical_midbody_root_plus_phase",
             "wheel_axle_relative_root_only","historical_midbody_relative_root_only",
             "wheel_axle_relative_root_plus_phase",
             "historical_midbody_relative_root_plus_phase",
             "static_2026_3d_mirror",
             "wheel_axle_root_only_mirror",
             "historical_midbody_root_only_mirror",
             "wheel_axle_relative_root_only_mirror",
             "historical_midbody_relative_root_only_mirror")


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def reference_relative_index(value:int, reference:int, states:int)->int:
    """One source-first angular/phase zero, not a recovered physical angle."""
    if (type(states) is not int or states not in (24,64) or
            any(type(x) is not int or not 0<=x<states
                for x in (value,reference))):
        raise ValueError("original source index/reference must share the correct 24/64-state table")
    return (value-reference)%states


def check_receipts(source_zip:bytes, pose_raw:bytes, axis_raw:bytes,
                   camera_raw:bytes) -> tuple[dict,dict,dict]:
    if (sha(source_zip)!=ZIP_SHA or sha(pose_raw)!=POSE_SHA or
            sha(axis_raw)!=AXIS_SHA or sha(camera_raw)!=CAMERA_SHA):
        raise ValueError("authenticated original source/camera SHA mismatch")
    # The SHA-locked original archive from #3103 includes its 97 exact
    # original emulator files. Its canonical auditor was introduced *after*
    # this model-controller branch split from main. Preserve the precise
    # entire-archive cryptographic oracle without copying that auditor into
    # a competing model branch. CRC and selected-file length/pose hashes are
    # independently checked below as additional fail-closed guards.
    with zipfile.ZipFile(io.BytesIO(source_zip)) as z:
        if z.testzip() is not None or len(z.namelist())!=97:
            raise ValueError("original Mesen24 archive member integrity failed")
    pose=json.loads(pose_raw)
    axis=json.loads(axis_raw)
    camera=json.loads(camera_raw)
    if (pose.get("original_usa_ROM_sha256")!=ROM_SHA or
            pose.get("original_Mesen24_source_archive_sha256")!=ZIP_SHA or
            pose.get("all_48_original_64x64_source_index_images_pixel_exact_from_ROM") is not True or
            axis.get("original_authenticated_USA_ROM_sha256")!=ROM_SHA or
            axis.get("original_ROM_24phase_64angle_exact_source_frame_count")!=1536):
        raise ValueError("original ROM exact presentation identity invalid")
    from tools.art.glb_parent_part_id_raster import validated_camera
    validated_camera(camera)
    return pose,axis,camera


def source_center(axis:dict) -> tuple[float,float]:
    boxes=axis.get("source_phase_variation_bbox_by_ROM_angle_index")
    if not isinstance(boxes,dict) or set(boxes)!={str(i) for i in range(64)}:
        raise ValueError("missing 64 source-only orientation region witnesses")
    centres=[]
    for n in range(0,64,2):  # predeclared even-orientation centre controls
        b=boxes[str(n)]
        if (type(b) is not list or len(b)!=4 or
                any(type(v) is not int for v in b) or
                not 0<=b[0]<=b[2]<64 or not 0<=b[1]<=b[3]<64):
            raise ValueError("invalid original ROM source region bounding box")
        centres.append(((b[0]+b[2])/2,(b[1]+b[3])/2))
    return (sum(x for x,_ in centres)/len(centres),
            sum(y for _,y in centres)/len(centres))


def rotate_source_2d(mask:bytes, offset:int, centre:tuple[float,float])->bytes:
    """One fixed original source-only 2D null; no re-registration by tick."""
    if len(mask)!=4096 or set(mask)-{0,1} or type(offset) is not int:
        raise ValueError("binary original 64px source and integer index offset required")
    x0,y0=centre
    a=2*math.pi*(offset%64)/64
    c,s=math.cos(a),math.sin(a)
    out=bytearray(4096)
    for y in range(64):
        for x in range(64):
            dx,dy=x-x0,y-y0
            sx=math.floor(x0+c*dx+s*dy+0.5)
            sy=math.floor(y0-s*dx+c*dy+0.5)
            if 0<=sx<64 and 0<=sy<64:
                out[y*64+x]=mask[sy*64+sx]
    return bytes(out)


def anchor(mask:bytes) -> tuple[int,int]:
    """Observed lowest visible alpha span, explicitly NOT ground contact."""
    if len(mask)!=4096 or set(mask)-{0,1}:
        raise ValueError("original source alpha mask malformed")
    y=max((k//64 for k,v in enumerate(mask) if v),default=-1)
    if y<0:raise ValueError("empty source silhouette")
    xs=[x for x in range(64) if mask[y*64+x]]
    return xs[0]+xs[-1],2*y


def source_horizontal_reflect4(mask4):
    """Reflect candidate along logical 64px *source-index centre* x2=63.

    The actual 4x source pixel centres are x=4*k+2. A naive 256x reverse
    maps them to 4*(63-k)+1 (one quarter source pixel off the sampling grid).
    Here source x -> 256-x preserves the x=4*k+2 centre lattice exactly;
    leftmost column is clipped rather than wrapped. Source model geometry
    must already be fully contained by the fixed camera.
    """
    import numpy as np
    if (not isinstance(mask4,np.ndarray) or mask4.shape!=(256,256)
            or mask4.dtype!=np.bool_):
        raise ValueError("one binary 256x256 real GLB projection required")
    out=np.zeros_like(mask4)
    out[:,1:]=mask4[:,255:0:-1]
    return out


def registered_mask4(model4, original_anchor:tuple[int,int],
                     neutral_anchor:tuple[int,int])->bytes:
    import numpy as np
    if model4.shape!=(256,256):
        raise ValueError("one 256x256 provisional-camera binary model mask required")
    dx=2*(original_anchor[0]-neutral_anchor[0])
    dy=2*(original_anchor[1]-neutral_anchor[1])
    ys,xs=np.nonzero(model4)
    if not len(xs):
        raise ValueError("no original GLB projected opaque pixels")
    nx,ny=xs+dx,ys+dy
    if min(nx)<0 or max(nx)>=256 or min(ny)<0 or max(ny)>=256:
        raise ValueError("single original alpha anchor would clip GLB; no auto-fit")
    canvas=np.zeros((256,256),dtype=bool)
    canvas[ny,nx]=True
    return bytes(canvas[2::4,2::4].astype(np.uint8).ravel())


def metric(source:bytes,candidate:bytes)->dict:
    if len(source)!=4096 or len(candidate)!=4096 or set(source)-{0,1} or set(candidate)-{0,1}:
        raise ValueError("actual 64px alpha source and model required")
    tp=sum(a==1 and b==1 for a,b in zip(source,candidate))
    fp=sum(a==0 and b==1 for a,b in zip(source,candidate))
    fn=sum(a==1 and b==0 for a,b in zip(source,candidate))
    return {"tp":tp,"fp":fp,"fn":fn,
            "iou":round(tp/(tp+fp+fn),8) if tp+fp+fn else 1.0}


def fixed_source_y_band_metrics(source:bytes,candidate:bytes)->dict:
    """One fixed partition of genuine original 64px source coordinates.

    No per-pose vertical crop, anatomical labeling, silhouette auto-fit or
    replacement of whole-mask IoU. Sum TP/FP/FN across bands = full mask.
    """
    if (len(source)!=4096 or len(candidate)!=4096 or
            set(source)-{0,1} or set(candidate)-{0,1}):
        raise ValueError("one binary original 64px pair required")
    result={}
    for name,y0,y1 in SOURCE_Y_BANDS:
        tp=fp=fn=0
        for y in range(y0,y1+1):
            for a,b in zip(source[y*64:y*64+64],candidate[y*64:y*64+64]):
                if a and b:tp+=1
                elif b:fp+=1
                elif a:fn+=1
        def centroid(plane):
            places=[(x,y) for y in range(y0,y1+1)
                    for x in range(64) if plane[y*64+x]]
            if not places:return None
            return [round(sum(x for x,_ in places)/len(places),4),
                    round(sum(y for _,y in places)/len(places),4)]
        result[name]={
            "tp":tp,"fp":fp,"fn":fn,
            "iou":round(tp/(tp+fp+fn),8) if tp+fp+fn else 1.0,
            "source_opaque_centroid_xy":centroid(source),
            "candidate_opaque_centroid_xy":centroid(candidate),
        }
    return result


def read_original_roles(source_zip:bytes,pose:dict)->dict:
    from tools.art.audit_original_mesen_oam_descriptors import decode_oam
    from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj
    frames={}
    with zipfile.ZipFile(io.BytesIO(source_zip)) as z:
        for role,(slot,palette) in ROLES.items():
            receipt=pose["per_original_source_racer"][role][
                "source_24_unique_per_tick_ROM_primary_frame_IDs"]
            lookup={row["authentic_original_bridge_tick"]:row for row in receipt}
            if set(lookup)!=set(range(1601,1625)):
                raise ValueError("original 24-tick exact frame sequence incomplete")
            frames[role]={}
            for t in [1601,*SELECTED[role]]:
                desc=decode_oam(z.read(f"frame-{t:06d}-oam.bin"))[slot]
                vram=z.read(f"frame-{t:06d}-vram.bin")
                cgram=z.read(f"frame-{t:06d}-cgram.bin")
                if len(vram)!=65536 or len(cgram)!=512:
                    raise ValueError("original Mesen24 PPU member byte length invalid")
                obj=decode_source_obj(desc,vram,cgram,
                    oam_mode=4,obj_base=0x6000,second_table_offset=0x1000)
                pose_row=lookup[t]
                phase=pose_row["source_primary_phase_index"]
                angle=pose_row["source_primary_angle_index"]
                if (obj["size"]!=64 or obj["slot"]!=slot or
                        obj["source_palette_id"]!=palette or
                        sha(obj["plane"])!=pose_row["source_held_OAM_local_index_plane_sha256"] or
                        type(phase) is not int or not 0<=phase<24 or
                        type(angle) is not int or not 0<=angle<64 or
                        pose_row["source_primary_frame_id"]!=64*phase+angle):
                    raise ValueError("original ROM frame ID and actual 4bpp PPU disagree")
                frames[role][t]={"phase":phase,"angle":angle,
                                 "alpha":bytes(obj["alpha_mask"])}
    return frames


def audit(source_zip:bytes,pose_raw:bytes,axis_raw:bytes,camera_raw:bytes,
          export_root:Path)->dict:
    import numpy as np
    import trimesh
    from tools.art.experimental_fixed_root_orbit import apply_root_scene
    from tools.art.render_racer_glb_projection import render_mask
    from tools.art.no_replace_report import publish_text_once  # existing no-replace standard
    pose,axis,camera=check_receipts(source_zip,pose_raw,axis_raw,camera_raw)
    src=read_original_roles(source_zip,pose)
    centre=source_center(axis)
    if (abs(centre[0]-31.515625)>0.02 or
            abs(centre[1]-19.5859375)>0.02):
        raise ValueError("previous original-ROM source orbit pivot changed")
    validate=runpy.run_path(str(Path(__file__).resolve().parent /
                                "model-review/stage_pages.py"))["validate"]
    pointer,outputs=validate(export_root,"upright")
    if pointer["source_sha256"]!=SCAD_SHA or sha(outputs["glb"].read_bytes())!=pointer["glb_sha256"]:
        raise ValueError("source-owned real 2026 model not authenticated")
    scene=trimesh.load(outputs["glb"],file_type="glb",force="scene",process=False)
    def model4(angle:int,pivot:str,drive:float):
        apply_root_scene(scene,angle,pivot,drive,0)
        geom=(scene.to_geometry() if callable(getattr(scene,"to_geometry",None))
              else scene.dump(concatenate=True))
        return render_mask(np.asarray(geom.vertices),np.asarray(geom.faces),camera).astype(bool)
    neutral=model4(0,"wheel_axle",0)
    neutral_mask=bytes(neutral[2::4,2::4].astype(np.uint8).ravel())
    neutral_anchor=anchor(neutral_mask)
    neutral_mirrored=source_horizontal_reflect4(neutral)
    neutral_mirrored_anchor=anchor(
        bytes(neutral_mirrored[2::4,2::4].astype(np.uint8).ravel()))
    anchors={role:anchor(rows[1601]["alpha"]) for role,rows in src.items()}
    original_refs={role:rows[1601] for role,rows in src.items()}
    model_masks={}
    scores={}
    for role,rows in src.items():
        scores[role]={}
        for t in SELECTED[role]:
            record=rows[t]
            relative_angle=reference_relative_index(
                record["angle"],original_refs[role]["angle"],64)
            relative_phase=reference_relative_index(
                record["phase"],original_refs[role]["phase"],24)
            predictions={
                "static_original_2d":original_refs[role]["alpha"],
                "source_original_2d_rotation":rotate_source_2d(
                    original_refs[role]["alpha"],
                    record["angle"]-original_refs[role]["angle"],centre),
                "static_2026_3d":registered_mask4(neutral,anchors[role],neutral_anchor),
                "static_2026_3d_mirror":registered_mask4(
                    neutral_mirrored,anchors[role],neutral_mirrored_anchor)
            }
            for pivot in PIVOTS:
                for label,model_angle,delta in (
                        ("root_only",record["angle"],0.),
                        ("root_plus_phase",record["angle"],15.*record["phase"]),
                        ("relative_root_only",relative_angle,0.),
                        ("relative_root_plus_phase",relative_angle,15.*relative_phase)):
                    key=(pivot,model_angle,delta)
                    if key not in model_masks:
                        model_masks[key]=model4(model_angle,pivot,delta)
                    predictions[pivot+"_"+label]=registered_mask4(
                        model_masks[key],anchors[role],neutral_anchor)
                    if label in ("root_only","relative_root_only"):
                        # A fixed alternative *candidate-only* image-space
                        # handedness null, scored for BOTH original players.
                        # Never silently apply original completed-screen red
                        # OAM reflection to held OAM-local source pixels.
                        predictions[pivot+"_"+label+"_mirror"]=registered_mask4(
                            source_horizontal_reflect4(model_masks[key]),
                            anchors[role],neutral_mirrored_anchor)
            if set(predictions)!=set(ARM_NAMES):
                raise ValueError("missing original 2D null or same real 3D candidate")
            scores[role][t]={
                "source_phase":record["phase"],"source_orientation":record["angle"],
                "source_relative_phase_index_from_tick1601":relative_phase,
                "source_relative_orientation_index_from_tick1601":relative_angle,
                "original_alpha_pixel_count":sum(record["alpha"]),
                "arms":{name:metric(record["alpha"],m)
                        for name,m in predictions.items()},
                "fixed_source_y_bands": {
                    name:fixed_source_y_band_metrics(record["alpha"],m)
                    for name,m in predictions.items()},
            }
            # Keep masks for exactly the predeclared original event comparisons.
            scores[role][t]["_masks"]={key:value for key,value in predictions.items()}
    results={}
    for name in ARM_NAMES:
        per_role={}
        for role,edges in EVENTS.items():
            metrics=[scores[role][t]["arms"][name] for t in SELECTED[role]]
            total={key:sum(m[key] for m in metrics) for key in ("tp","fp","fn")}
            change=[]
            for a,b in edges:
                source_change=bytes(x!=y for x,y in zip(src[role][a]["alpha"],src[role][b]["alpha"]))
                model_change=bytes(x!=y for x,y in zip(
                    scores[role][a]["_masks"][name], scores[role][b]["_masks"][name]))
                change.append({"actual_source_ticks":[a,b],
                               "source_change_pixels":sum(source_change),
                               "model_change_pixels":sum(model_change),
                               "fixed_source_y_bands":fixed_source_y_band_metrics(
                                   source_change,model_change),
                               **metric(source_change,model_change)})
            per_bands={}
            for band,y0,y1 in SOURCE_Y_BANDS:
                instances=[scores[role][t]["fixed_source_y_bands"][name][band]
                           for t in SELECTED[role]]
                counts={key:sum(a[key] for a in instances)
                        for key in ("tp","fp","fn")}
                union=sum(counts.values())
                per_bands[band]={**counts,"pooled_iou":
                    round(counts["tp"]/union,8) if union else 1.0}
            per_role[role]={
                "pooled_fixed_source_y_band_alpha":per_bands,
                "fixed_original_alpha_registration_x2y2":list(anchors[role]),
                "full_source_observations":len(metrics),
                "pooled_alpha_iou":round(total["tp"]/sum(total.values()),8),
                "mean_alpha_iou":round(sum(m["iou"] for m in metrics)/len(metrics),8),
                "alpha_tp_fp_fn":total,"actual_source_edge_change":change,
            }
        results[name]=per_role
    for role,rows in scores.items():
        for record in rows.values():
            del record["_masks"]
    return {
        "schema":SCHEMA,"original_ROM_SHA256":ROM_SHA,
        "source_consecutive_Mesen24_zip_SHA256":ZIP_SHA,
        "original_exact_ROM_frame_ID_report_SHA256":POSE_SHA,
        "original_full_24x64_source_axis_report_SHA256":AXIS_SHA,
        "original_source_7_6_fixed_camera_SHA256":CAMERA_SHA,
        "model_source_2026_SCAD_sha256":SCAD_SHA,
        "model_verified_actual_upright_GLB_sha256":pointer["glb_sha256"],
        "one_camera_no_per_frame_shift_or_pose_fit":True,
        "one_source_lower_alpha_anchor_per_player_not_ground_contact":True,
        "source_original_red_and_blue_OAM_local_not_completed_screen":True,
        "unverified_physical_2026_wheel_deg_per_source_phase":15,
        "unverified_physical_2026_root_angle_deg_per_source_index":360/64,
        "source_first_tick_absolute_and_relative_rig_controls_both_scored":True,
        "source_original_tick1601_reference_phase_orientation_by_player":{
            role:{"phase":r["phase"],"orientation":r["angle"]}
            for role,r in original_refs.items()},
        "original_1994_3D_geometry_camera_or_pose_recovered":False,
        "source_2026_character_likeness_owner_approved":False,
        "fixed_original_64px_y_bands":{
            name:[y0,y1] for name,y0,y1 in SOURCE_Y_BANDS},
        "fixed_y_bands_are_image_regions_not_verified_3D_anatomy":True,
        "source_OAM_local_candidate_horizontal_mirror_is_alternative_not_canonical_3D":True,
        "same_model_mirror_null_measured_for_both_players_no_best_per_frame":True,
        "source_frames":scores,"arms":results,
        "actual_root_render_cache_entries":len(model_masks),
        "experimental_hypotheses_are_retrospective_not_blind":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--pose-report",type=Path,required=True)
    p.add_argument("--axis-report",type=Path,required=True)
    p.add_argument("--camera",type=Path,required=True)
    p.add_argument("--verified-exports",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    record=audit(args.source_zip.read_bytes(),args.pose_report.read_bytes(),
                 args.axis_report.read_bytes(),args.camera.read_bytes(),
                 args.verified_exports)
    from tools.art.no_replace_report import publish_text_once
    publish_text_once(args.out,json.dumps(record,indent=2,sort_keys=True)+"\n")
    print("ART4K_ORIGINAL_REAL_GLB_FIXED_Y_BAND_DIAGNOSTIC",
          json.dumps({
              arm:{role:row["pooled_fixed_source_y_band_alpha"]
                   for role,row in record["arms"][arm].items()}
              for arm in ("source_original_2d_rotation","static_2026_3d",
                          "wheel_axle_root_only","historical_midbody_root_only",
                          "wheel_axle_relative_root_only",
                          "historical_midbody_relative_root_only",
                          "static_2026_3d_mirror",
                          "wheel_axle_root_only_mirror",
                          "historical_midbody_relative_root_only_mirror")},
              sort_keys=True))
    print("ART4K_ORIGINAL_REAL_GLB_FIXED_PIVOT_VS_2D",
          json.dumps({arm:{role:{key:row[key] for key in
              ("pooled_alpha_iou","mean_alpha_iou")}
              for role,row in per.items()}
              for arm,per in record["arms"].items()},sort_keys=True))


if __name__=="__main__":
    main()
