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
ARM_NAMES = ("static_original_2d","source_original_2d_rotation",
             "static_2026_3d","wheel_axle_root_only",
             "historical_midbody_root_only",
             "wheel_axle_root_plus_phase","historical_midbody_root_plus_phase")


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def check_receipts(source_zip:bytes, pose_raw:bytes, axis_raw:bytes,
                   camera_raw:bytes) -> tuple[dict,dict,dict]:
    if (sha(source_zip)!=ZIP_SHA or sha(pose_raw)!=POSE_SHA or
            sha(axis_raw)!=AXIS_SHA or sha(camera_raw)!=CAMERA_SHA):
        raise ValueError("authenticated original source/camera SHA mismatch")
    from tools.art.audit_original_mesen_contiguous_24 import audit as audit_mesen
    verified=audit_mesen(source_zip)
    if verified["source_canonical_archive_sha256"]!=ZIP_SHA:
        raise ValueError("original Mesen archive member-hash verification failed")
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
                obj=decode_source_obj(desc,
                    z.read(f"frame-{t:06d}-vram.bin"),
                    z.read(f"frame-{t:06d}-cgram.bin"),
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
    anchors={role:anchor(rows[1601]["alpha"]) for role,rows in src.items()}
    original_refs={role:rows[1601] for role,rows in src.items()}
    model_masks={}
    scores={}
    for role,rows in src.items():
        scores[role]={}
        for t in SELECTED[role]:
            record=rows[t]
            predictions={
                "static_original_2d":original_refs[role]["alpha"],
                "source_original_2d_rotation":rotate_source_2d(
                    original_refs[role]["alpha"],
                    record["angle"]-original_refs[role]["angle"],centre),
                "static_2026_3d":registered_mask4(neutral,anchors[role],neutral_anchor)
            }
            for pivot in PIVOTS:
                for label,delta in (("root_only",0.),("root_plus_phase",15.*record["phase"])):
                    key=(pivot,record["angle"],delta)
                    if key not in model_masks:
                        model_masks[key]=model4(record["angle"],pivot,delta)
                    predictions[pivot+"_"+label]=registered_mask4(
                        model_masks[key],anchors[role],neutral_anchor)
            if set(predictions)!=set(ARM_NAMES):
                raise ValueError("missing original 2D null or same real 3D candidate")
            scores[role][t]={
                "source_phase":record["phase"],"source_orientation":record["angle"],
                "original_alpha_pixel_count":sum(record["alpha"]),
                "arms":{name:metric(record["alpha"],m)
                        for name,m in predictions.items()}
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
                               **metric(source_change,model_change)})
            per_role[role]={
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
        "original_1994_3D_geometry_camera_or_pose_recovered":False,
        "source_2026_character_likeness_owner_approved":False,
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
    print("ART4K_ORIGINAL_REAL_GLB_FIXED_PIVOT_VS_2D",
          json.dumps({arm:{role:{key:row[key] for key in
              ("pooled_alpha_iou","mean_alpha_iou")}
              for role,row in per.items()}
              for arm,per in record["arms"].items()},sort_keys=True))


if __name__=="__main__":
    main()
