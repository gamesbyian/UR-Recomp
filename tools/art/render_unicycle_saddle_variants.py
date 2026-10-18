#!/usr/bin/env python3
"""Unapproved original-title saddle silhouette alternatives, one canonical rig.

Never fit a physical wheel diameter from the title source: the wheel's top
is occluded by the racer/rainbow, and the title camera is not orthographic.
The original render is referenced through a hash-bound AOT archive, not
distributed or used to authorize material/physics/runtime changes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
try:
    from .render_shared_unicycle_review import (
        inspect_model, authentic_sources, open_p7,
    )
except ImportError:
    from render_shared_unicycle_review import (
        inspect_model, authentic_sources, open_p7,
    )

SPANS = (1.0, 1.4, 1.8, 2.2)
CAMERA = "0,0,1.6,90,0,0,12.5"
SIZE = 400

def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def prove_parameters(text: str) -> None:
    if (text.count("rig_frame_mass=is_undef") != 1 or
        text.count("module frame_member(") != 1 or
        text.count("rig_frame_mass <= 2") != 1 or
        text.count("rig_frame_mass >= 1") != 1 or
        if (text.count("rig_saddle_span=is_undef") != 1 or
        text.count("scale([rig_saddle_span,1,1])") != 1 or
        'rig_saddle_span <= 2.2' not in text or
        'rig_saddle_span >= 1' not in text or
        text.count('rig(rig_pose);') != 1):
        raise ValueError("saddle sweep no longer shares one bounded canonical rig")

def preview(model: Path, out: Path, source_zip: Path | None = None,
            openscad: str = "openscad", xvfb: bool = False, frame_mass: float = 1.0):
    from PIL import Image, ImageDraw, ImageEnhance
    inspect_model(model)
    prove_parameters(model.read_text(encoding="utf-8"))
    if frame_mass not in (1.0, 1.4, 1.8, 2.0):
        raise ValueError("non-reviewed fork mass outside bounded visual alternatives")
    if out.exists() and any(out.iterdir()):
        raise ValueError("output directory must be new or empty")
    original = authentic_sources(source_zip) if source_zip else None
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for span in SPANS:
        image = out/f"saddle-span-{span:.1f}.png"
        argv=(["xvfb-run", "-a"] if xvfb else [])+[
            openscad, "--hardwarnings", "-o", str(image),
            f"--imgsize={SIZE},{SIZE}", "--projection=o",
            "--colorscheme=Tomorrow", f"--camera={CAMERA}",
            "-D", 'rig_pose="upright"',
            "-D", f"rig_saddle_span={span}",
            "-D", f"rig_frame_mass={frame_mass}", str(model)]
        result=subprocess.run(argv,capture_output=True,text=True,timeout=90)
        if result.returncode:
            raise ValueError("original CAD saddle study failed: "+result.stderr[-300:])
        with Image.open(image) as im:
            if im.size != (SIZE,SIZE):
                raise ValueError("unexpected source model image")
            bg=im.convert("RGB").getpixel((0,0))
            # The saddle is the dark body above Y=110, before the wheel.
            pixels=im.convert("RGB").load()
            saddle=[(x,y) for y in range(0,110) for x in range(SIZE)
                    if max(pixels[x,y]) < 125]
            if not saddle:
                raise ValueError("saddle not visible in common camera")
            left,right=min(x for x,y in saddle),max(x for x,y in saddle)
            if left<4 or right>SIZE-5:
                raise ValueError("candidate saddle clipped by fixed camera")
        records.append({"scale":span,"file":image.name,"sha256":hash_file(image),
                        "camera":CAMERA,
                        "candidate_dark_saddle_projected_width_px":right-left+1})
    panel_height=SIZE+(250 if original else 0)+75
    canvas=Image.new("RGB",(SIZE*len(SPANS),panel_height),"#f5f6f8")
    d=ImageDraw.Draw(canvas)
    y0=0
    if original:
        title=open_p7(original["original_title"]).convert("RGB")
        # The source is truly 256x224; 7:6 PAR + display-only 3x
        # brightness are *not* a transform used for equality judgments.
        title=title.resize((round(title.width*7/6),title.height),
                           Image.Resampling.NEAREST)
        title=ImageEnhance.Brightness(title).enhance(3.0)
        title.thumbnail((430,220),Image.Resampling.NEAREST)
        canvas.paste(title,(12,16))
        d.text((450,12),"Real 1994 title source, guest 400",fill="#161616")
        d.text((450,36),"Unknown camera and occluded wheel top",fill="#161616")
        d.text((450,60),"Unapproved saddle-width silhouette study",fill="#161616")
        d.text((450,84),"No physical-model width ratio inferred",fill="#161616")
        y0=250
    for i,row in enumerate(records):
        image=Image.open(out/row["file"]).convert("RGB")
        canvas.paste(image,(SIZE*i,y0))
        d.text((SIZE*i+8,y0+SIZE+10),
               f"Same rig | seat span {row['scale']:.1f} | width {row['candidate_dark_saddle_projected_width_px']}px",
               fill="#181818")
        image.thumbnail((32,32),Image.Resampling.LANCZOS)
        canvas.paste(image,(SIZE*i+8,y0+SIZE+32))
    d.text((10,panel_height-24),"NO HUMAN VISUAL APPROVAL | NO GAME RENDERER/GEOMETRY CHANGES",fill="#181818")
    sheet=out/"single-rig-saddle-variants.png";canvas.save(sheet)
    report={"schema":"UR-racer-canonical-saddle-span-hypotheses/1",
            "model_sha256":hash_file(model),
            "contact_sha256":hash_file(sheet),
            "source_archive_sha256":hash_file(source_zip) if source_zip else None,
            "camera":CAMERA,"same_model_no_replacement_art_merged":True,
            "candidate_count":len(records),"candidates":records,
            "bounded_frame_mass":frame_mass,
            "original_title_wheel_top_unmeasurable_occluded":True,
            "title_camera_perspective_unknown":True,
            "comparative_cad_geometry_not_verified_likeness":True,
            "original_source_3d_dimensions_inferred":False,
            "owner_visual_approval":False,
            "shipping_art_approved":False,"release_accepted":False}
    (out/"saddle-variants-receipt.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n")
    return sheet,report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model",type=Path,
                   default=Path(__file__).parent/"candidates"/"unicycle_shared_rig.scad")
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--authentic-source-zip",type=Path)
    p.add_argument("--openscad",default="openscad")
    p.add_argument("--xvfb",action="store_true")
    p.add_argument("--frame-mass",type=float,choices=(1.0,1.4,1.8,2.0),default=1.0,
                   help="same rig, one bounded pre-rendered frame-bulk proposal")
    a=p.parse_args()
    sheet, report=preview(a.model.resolve(),a.out.resolve(),
                          a.authentic_source_zip.resolve() if a.authentic_source_zip else None,
                          a.openscad,a.xvfb,a.frame_mass)
    print(f"UR_UNAPPROVED_SADDLE_VARIANTS {sheet} "
          f"SHA256={report['contact_sha256']} human_approved=0")

if __name__=="__main__":
    main()
