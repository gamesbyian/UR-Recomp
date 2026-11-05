#!/usr/bin/env python3
"""Export nonshipping 2D print figure crops from ONE authenticated USA manual.

The source PDF is official period illustration, not original 1994 3D meshes,
camera or original-model material identity. Output landmark templates are
deliberately incomplete until a human actually annotates visible parts.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile

SCHEMA="UR-ART4K-ORIGINAL-MANUAL-PRINT-CROPS/1"
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"reference/imported/manuals/Uniracers-USA-manual.pdf"
SOURCE_BLOB_SHA1="a52da4f94a75e3e76fd61a759cb8e0c3a4fbc5d3"
SOURCE_URL="https://github.com/gamesbyian/UR-Recomp/blob/main/reference/imported/manuals/Uniracers-USA-manual.pdf"
BASIS=(1024,1497)
DPI=144
PAGE_COUNT=40
# Rectangles identified visually on the original official manual pages.
# This is *not* a wheel/saddle bounding-box fit or a 3D camera calibration.
FIGURES=(
 ("p14-twist-fork-front",13,(652,180,982,521),"front",
  "near-frontal cyan fork with wheel occluded by printed ribbon"),
 ("p14-zee-flip-oblique",13,(451,756,912,1107),"three-quarter",
  "red stunt, wheel/axle partly obscured by printed ribbon"),
 ("p15-mega-underside",14,(192,409,1024,1473),"three-quarter",
  "large cyan wheel/hub/crank and saddle underside; right edge clips pedal"),
 ("p16-menu-saddle",15,(580,0,1020,367),"three-quarter",
  "red side-lean saddle/stem and wheel with print-text overlap"),
)


def git_blob_sha1(raw:bytes)->str:
    if type(raw) is not bytes:
        raise ValueError("original PDF bytes required")
    return hashlib.sha1(("blob "+str(len(raw))+"\0").encode()+raw).hexdigest()


def authenticate_pdf(raw:bytes, expected:str=SOURCE_BLOB_SHA1)->dict:
    if (type(raw) is not bytes or not 0<len(raw)<=64*1024*1024
            or not raw.startswith(b"%PDF-") or type(expected) is not str
            or len(expected)!=40 or any(x not in "0123456789abcdef" for x in expected)
            or git_blob_sha1(raw)!=expected):
        raise ValueError("requires exact Git-tracked original 1994 USA manual PDF")
    return {"source_git_blob_sha1":expected,
            "source_pdf_sha256":hashlib.sha256(raw).hexdigest(),
            "source_pdf_size":len(raw)}


def crop_box(page_width:int,page_height:int,box:tuple)->tuple[int,int,int,int]:
    if (type(page_width) is not int or type(page_height) is not int
            or not 128<=page_width<=30000 or not 128<=page_height<=30000
            or type(box) is not tuple or len(box)!=4
            or any(type(n) is not int for n in box)):
        raise ValueError("invalid original page dimensions or manual crop bounds")
    x0,y0,x1,y1=box
    if not(0<=x0<x1<=BASIS[0] and 0<=y0<y1<=BASIS[1]):
        raise ValueError("original printed page crop is inverted or out of bounds")
    result=(round(x0*page_width/BASIS[0]),round(y0*page_height/BASIS[1]),
            round(x1*page_width/BASIS[0]),round(y1*page_height/BASIS[1]))
    a,b,c,d=result
    if not(0<=a<c<=page_width and 0<=b<d<=page_height
           and c-a>=32 and d-b>=32):
        raise ValueError("degenerate output page crop")
    return result


def extract(raw:bytes, target:Path)->dict:
    """Render from independently authenticated bytes into an all-or-none new dir.

    This low-level helper accepts synthetic PDFs for unit testing. The public
    CLI always calls authenticate_pdf on the tracked original source first.
    """
    try:
        import fitz
        from PIL import Image
    except ImportError as e:
        raise RuntimeError("PyMuPDF and Pillow required for offline manual crops") from e
    if not isinstance(target,Path):
        raise ValueError("local output path required")
    target=target.resolve()
    if target.exists():
        raise FileExistsError("source evidence directory exists: no overwrite")
    if not target.parent.is_dir():
        raise ValueError("parent output directory must already exist")
    staged=Path(tempfile.mkdtemp(prefix=".original-manual-views-",dir=target.parent))
    try:
        doc=fitz.open(stream=raw,filetype="pdf")
        try:
            if doc.page_count!=PAGE_COUNT or doc.is_encrypted:
                raise ValueError("incorrect original manual pagination")
            images={}
            output=[]
            digest=hashlib.sha256(raw).hexdigest()
            for label,index,region,angle,limits in FIGURES:
                if index not in images:
                    page=doc.load_page(index)
                    raster=page.get_pixmap(matrix=fitz.Matrix(DPI/72,DPI/72),
                                           colorspace=fitz.csRGB,alpha=False)
                    images[index]=Image.frombytes("RGB",(raster.width,raster.height),
                                                   raster.samples)
                image=images[index]
                bounds=crop_box(*image.size,region)
                stream=io.BytesIO()
                image.crop(bounds).save(stream,format="PNG",compress_level=9)
                encoded=stream.getvalue()
                (staged/(label+".png")).write_bytes(encoded)
                output.append({
                    "reference_id":label,"original_printed_page":index+1,
                    "original_pdf_zero_based_page":index,"reference_image_basis":list(BASIS),
                    "full_page_rendered_pixels":list(image.size),
                    "page_crop_basis_xyxy":list(region),"page_crop_pixels_xyxy":list(bounds),
                    "crop_png":label+".png",
                    "crop_png_sha256":hashlib.sha256(encoded).hexdigest(),
                    "approximate_print_view":angle,
                    "printed_occlusion_and_perspective_limit":limits,
                    "historical_3d_camera_or_material_identity_verified":False,
                    "human_landmarks_measured":False,
                })
        finally:
            doc.close()
        report={
            "schema":SCHEMA,"source_git_blob_sha1":git_blob_sha1(raw),
            "source_pdf_sha256":digest,"source_pdf_size_bytes":len(raw),
            "source_pdf_url":SOURCE_URL,"printed_manual_page_count":PAGE_COUNT,
            "render_dpi":DPI,"figures":output,
            "same_historical_3d_mesh_as_source_game_proven":False,
            "human_likeness_approved":False,"shipping_art_approved":False,
            "manual_print_poses_blind_3d_holdout":False,
        }
        (staged/"source-crops.json").write_text(
            json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        template={"schema":"UR-RACER-LIKENESS-LANDMARKS/1","views":[]}
        for fig in output:
            template["views"].append({
                "id":fig["reference_id"],
                "image":{"path":fig["crop_png"],"sha256":fig["crop_png_sha256"]},
                "source":{"url":SOURCE_URL,"kind":"official-manual",
                    "creator_or_credit":"Nintendo/DMA Design official 1994 print art",
                    "region_or_version":"1994 USA instruction booklet",
                    "capture_context":"printed page "+str(fig["original_printed_page"])
                       +"; "+fig["printed_occlusion_and_perspective_limit"],
                    "rights_notes":"Original copyrighted illustration, local study only"},
                "view":{"angle":fig["approximate_print_view"],
                    "pose":"1994 print illustration, no gameplay ROM pose correspondence",
                    "pixel_aspect":"square",
                    "crop_and_rescale_history":"full PDF SHA256 "+digest+
                    "; 144 DPI; original PDF page "+str(fig["original_pdf_zero_based_page"])
                    +"; crop "+str(fig["page_crop_pixels_xyxy"])},
                "annotator":"UNANNOTATED (replace with independent reviewer)",
                "landmarks":{},"unmeasurable":{},
            })
        # The existing projected 2D landmark validator must reject all
        # template entries until genuine visible coordinates are supplied.
        (staged/"landmarks.UNANNOTATED.json").write_text(
            json.dumps(template,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        if target.exists():
            raise FileExistsError("new manual crop destination appeared during extraction")
        os.rename(staged,target)
        return report
    finally:
        if staged.exists():
            shutil.rmtree(staged)


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf",type=Path,default=SOURCE)
    parser.add_argument("--out-dir",type=Path,required=True)
    args=parser.parse_args()
    raw=args.pdf.read_bytes()
    authentic=authenticate_pdf(raw)
    report=extract(raw,args.out_dir)
    if authentic["source_pdf_sha256"]!=report["source_pdf_sha256"]:
        raise ValueError("original manual changed after authentication")
    print(json.dumps({"source_pdf_sha256":authentic["source_pdf_sha256"],
                      "extracted_views":len(report["figures"]),
                      "local_output":str(args.out_dir)},sort_keys=True))


if __name__=="__main__":
    main()
