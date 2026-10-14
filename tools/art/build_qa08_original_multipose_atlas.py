#!/usr/bin/env python3
"""Hash-bound source-only 2P multi-pose contact atlas from original native AOT.

Renders verified Original isolated OBJ sources at 1872,1888,2208. Never builds
a 3D likeness, invents hidden geometry or asserts final PPU source ownership.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import zipfile

try:
    from tools.art.build_qa08_original_contact_sheet import display_rgba, header
except ModuleNotFoundError:
    from build_qa08_original_contact_sheet import display_rgba, header

FRAMES = (1872, 1888, 2208)
SLOTS = (98, 99, 96, 97)
FRAME_LABEL = {1872:"Real 2P countdown", 1888:"Moving countdown", 2208:"Post-GO"}
WIDTH, HEIGHT = 342, 224


def source_sample(z: zipfile.ZipFile, frame: int, slot: int) -> tuple[dict, bytes, set]:
    name=f"baldosa-evidence/ws342_obj_slot_{slot}_frame{frame}.json"
    evidence=json.loads(z.read(name))
    src=evidence["source"]
    if (evidence.get("status") != "passed" or
            evidence.get("differing_original_rasters") != [] or
            evidence.get("identical_complete_original_342_rasters") != 7 or
            evidence.get("source_log_matches_pam") is not True or
            evidence.get("shared_full_frame_guest_ids") !=
            [1808,1824,1840,1856,1872,1888,2208] or
            src.get("guest_frame") != frame or src.get("slot") != slot or
            src.get("source_nonempty") is not True):
        raise ValueError("source is not the exact independent original/native 2P witness")
    image_name=(f"baldosa-ws342-obj-slots/"
                f"ur-baldosa-ws342-obj-slot{slot}-frame{frame:06d}.pam")
    data=z.read(image_name)
    hdr=header(WIDTH,HEIGHT)
    if not data.startswith(hdr) or len(data) != len(hdr)+WIDTH*HEIGHT*4:
        raise ValueError("not real unscaled original native P7 source")
    rgba=data[len(hdr):]
    source_hash=hashlib.sha256(rgba).hexdigest()
    if source_hash != src["source_sha256"]:
        raise ValueError("original OAM source raster SHA256 differs from report")
    opaque={
        (i//4%WIDTH,i//4//WIDTH)
        for i in range(3,len(rgba),4) if rgba[i] != 0
    }
    top=sum(1 for x,y in opaque if y<112)
    bottom=len(opaque)-top
    if top != src["top_opaque_source_pixels"] or bottom != src["bottom_opaque_source_pixels"]:
        raise ValueError("genuine PPU alpha counts differ from accepted source report")
    box=[min(x for x,y in opaque),min(y for x,y in opaque),
         max(x for x,y in opaque),max(y for x,y in opaque)]
    if box != src["bbox"]:
        raise ValueError("source PPU alpha bbox differs from report")
    return src, rgba, opaque


def relative_jaccard(first: set, first_box: list[int],
                     second: set, second_box: list[int]) -> dict:
    """Exact binary-shape comparison after bbox origin registration, not 3D."""
    a={(x-first_box[0],y-first_box[1]) for x,y in first}
    b={(x-second_box[0],y-second_box[1]) for x,y in second}
    intersect=len(a & b)
    union=len(a | b)
    if union == 0:
        raise ValueError("no real source pixels to compare")
    return {
        "shared_original_mask_pixels_after_bbox_alignment":intersect,
        "union_original_mask_pixels_after_bbox_alignment":union,
        "source_shape_Jaccard_after_bbox_origin_alignment":round(intersect/union,6),
        "screen_translation_source_xy":[second_box[0]-first_box[0],
                                         second_box[1]-first_box[1]],
        "source_mask_not_reconstructed_3d_geometry":True,
    }


def build(artifact: Path, dest: Path) -> dict:
    rows={}
    cards=[]
    with zipfile.ZipFile(artifact) as z:
        for frame in FRAMES:
            for slot in SLOTS:
                source,rgba,opaque=source_sample(z,frame,slot)
                x0,y0,x1,y1=source["bbox"]
                left=max(0,x0-4)
                top=max(0,y0-4)
                right=min(WIDTH-1,x1+4)
                bottom=min(HEIGHT-1,y1+4)
                cw,ch=right-left+1,bottom-top+1
                crop=b"".join(
                    rgba[4*(y*WIDTH+left):4*(y*WIDTH+right+1)]
                    for y in range(top,bottom+1)
                )
                if len(crop) != cw*ch*4:
                    raise ValueError("source crop lost original native pixels")
                key=f"{frame}-{slot}"
                rows[key]={
                    "guest_frame":frame,"original_oam_slot":slot,
                    "viewport":"upper" if slot in (98,99) else "lower",
                    "front_in_split_pair":slot in (96,98),
                    "original_native_rgba_sha256":source["source_sha256"],
                    "original_source_bbox_xyxy":source["bbox"],
                    "unmodified_alpha_pixel_count":len(opaque),
                    "visual_crop_rgba_sha256":hashlib.sha256(crop).hexdigest(),
                    "visual_crop_xyxy":[left,top,right,bottom],
                }
                label=(f"{FRAME_LABEL[frame]} / guest{frame} / "
                       f"{'upper' if slot>=98 else 'lower'} slot{slot} "
                       f"({'front' if slot in (96,98) else 'rear'})")
                image=display_rgba(crop,cw,ch,8)
                cards.append(
                    f'<section><h2>{html.escape(label)}</h2>'
                    f'<p>Source alpha {len(opaque)} pixels; bbox {source["bbox"]}</p>'
                    f'<div class="pane">{image}</div></section>'
                )
    changes={}
    with zipfile.ZipFile(artifact) as z:
        for slot in SLOTS:
            for a,b in zip(FRAMES,FRAMES[1:]):
                one,_,alpha_a=source_sample(z,a,slot)
                two,_,alpha_b=source_sample(z,b,slot)
                changes[f"slot{slot}:{a}->{b}"]=relative_jaccard(
                    alpha_a,one["bbox"],alpha_b,two["bbox"])
    # The two viewports encode the same two authentic source poses in
    # opposite OAM slot classes. Compare complete unscaled RGBA *within the
    # exact native alpha bounding rectangle*, including transparent pixels.
    # This normalizes ONLY translation, never rotation, colour or frame phase.
    mirrored = {}
    with zipfile.ZipFile(artifact) as z:
        for frame in FRAMES:
            for upper, lower in ((98,97),(99,96)):
                def canonical(slot):
                    source, rgba, _ = source_sample(z,frame,slot)
                    left,top,right,bottom = source["bbox"]
                    crop = b"".join(
                        rgba[4*(y*WIDTH+left):4*(y*WIDTH+right+1)]
                        for y in range(top,bottom+1)
                    )
                    return source["bbox"],crop
                first_box, first_rgba = canonical(upper)
                last_box, last_rgba = canonical(lower)
                if (first_box[2]-first_box[0] !=
                        last_box[2]-last_box[0] or
                        first_box[3]-first_box[1] !=
                        last_box[3]-last_box[1] or
                        first_rgba != last_rgba):
                    raise ValueError("paired upper/lower original PPU source RGBA alias differs")
                mirrored[f"{frame}:{upper}->{lower}"] = {
                    "bbox_registered_original_RGBA_exact": True,
                    "shared_bbox_RGBA_SHA256": hashlib.sha256(first_rgba).hexdigest(),
                    "native_translation_xy":[last_box[0]-first_box[0],
                                             last_box[1]-first_box[1]],
                    "not_a_final_PPU_winner_or_3D_identity": True,
                }
    report={
        "schema":"qa08-native-original-2p-multipose-foreground-source-atlas/1",
        "frames":list(FRAMES),"original_OAM_slots":list(SLOTS),
        "original_source_planes_authenticated":12,
        "original_source_pixel_aspect":"7:6",
        "frame_capture_phase":{"1872":"countdown","1888":"countdown moving",
                               "2208":"post-GO"},
        "actual_final_BG_OBJ_winner_proven":False,
        "original_hardware_validation":False,
        "procedural_HD_character_approved":False,
        "source_planes":rows,
        "registered_alpha_shape_change":changes,
        "six_exact_cross_viewport_source_RGBA_aliases":mirrored,
    }
    css=(
        "body{font:15px system-ui;margin:24px;background:#171b23;color:#e7ebf4}"
        "main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}"
        "section{background:#28313e;padding:10px;border:1px solid #566175}"
        "h2{font-size:14px}p{line-height:1.5}.pane{text-align:center;"
        "overflow:auto;background:repeating-conic-gradient(#485360 0% 25%,"
        "#27313a 0% 50%) 50%/16px 16px}.pane img{max-width:100%;"
        "height:auto;image-rendering:pixelated}@media(max-width:900px)"
        "{main{grid-template-columns:1fr}}"
    )
    page=(
        "<!DOCTYPE html><html lang=\"en\"><meta charset=\"utf-8\">"
        "<title>Original native unicycle 2P source pose atlas</title>"
        "<style>"+css+"</style>"
        "<h1>Original native unicycles: 2P source pose sequence</h1>"
        "<p>12 exact source-isolated SNES PPU OAM rasters from the existing "
        "accepted USA 2P native witness, not invented HD art. "
        "Positions and source colours are unmodified. Rendered display width "
        "uses 7:6 pixel aspect. Foreground priority and original physical "
        "SNES hardware remain independent gates. HTML order: each guest "
        "frame's front/rear upper pair then front/rear lower pair.</p>"
        "<main>"+"".join(cards)+"</main></html>"
    )
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(page,encoding="utf8")
    dest.with_suffix(".json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return report


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifact",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    r=build(a.artifact,a.out)
    print("QA08_NATIVE_ORIGINAL_MULTI_POSE_SOURCE_ACCEPTED "
          f"planes={r['original_source_planes_authenticated']} "
          "native=12 original=true source_owner=unproven art_approved=0")


if __name__=="__main__":
    main()
