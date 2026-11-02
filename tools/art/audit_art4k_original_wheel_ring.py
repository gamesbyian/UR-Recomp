#!/usr/bin/env python3
"""Bounded original-ROM *raster* wheel-ring anchor, not a recovered 3D axle.

Reads authenticated original USA ROM-composed 64x64 RGBA PNGs from the
previous original-source artifact. All original source/PNG/alpha/binary SHA
bytes are checked before reporting pixel positions. Does NOT infer historical
source animation chronology from authored reference windows.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

try:
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from no_replace_report import publish_text_once

CORPUS_MANIFEST_SHA256 = "e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e"
ORIGINAL_ROM_SHA256 = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SCHEMA = "UR-ART4K-ORIGINAL-ROM-2D-GREY-RING-CANDIDATES/1"
SOURCE_CORPUS_SCHEMA = "UR-RACER-ROM-COMPOSED-SOURCE-CORPUS/1"
SAMPLES = 48
# This explicitly constrained hypothesis uses source RASTER coordinates only.
X_MIN, X_MAX = 14, 49
Y_MIN, Y_MAX = 22, 34
R_MIN, R_MAX = 6, 10
MIN_GREY_RING_HITS = 36
OFFSETS = {
    radius: tuple((round(radius*math.cos(2*math.pi*i/SAMPLES)),
                   round(radius*math.sin(2*math.pi*i/SAMPLES)))
                  for i in range(SAMPLES))
    for radius in range(R_MIN,R_MAX+1)
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ring_candidates(rgba: bytes) -> dict:
    """Return ALL equally high scoring candidate centres, not a false unique axle."""
    if not isinstance(rgba,bytes) or len(rgba)!=64*64*4:
        raise ValueError("expected exactly 64x64 source RGBA bytes")
    gray=bytearray(64*64)
    for i in range(64*64):
        r,g,b,a=rgba[4*i:4*i+4]
        if a not in (0,255):
            raise ValueError("source must have binary alpha")
        gray[i]=int(a==255 and max(r,g,b)-min(r,g,b)<=3)
    maximum=-1
    tied=[]
    for radius, offsets in OFFSETS.items():
        for cy in range(Y_MIN,Y_MAX+1):
            for cx in range(X_MIN,X_MAX+1):
                hit=sum(gray[(cy+dy)*64+cx+dx] for dx,dy in offsets)
                if hit>maximum:
                    maximum=hit
                    tied=[[cx,cy,radius]]
                elif hit==maximum:
                    tied.append([cx,cy,radius])
    if maximum<MIN_GREY_RING_HITS:
        raise ValueError("insufficient occupied neutral-grey wheel-ring evidence")
    tied.sort()
    return {
        "max_neutral_ring_hits":maximum,
        "circumference_raster_samples":SAMPLES,
        "best_candidate_centres_xy_radius_logical_px":tied,
        "unique_candidate":len(tied)==1,
        "not_an_original_3d_axle":True,
    }


def validate_corpus_and_measure(source_zip: Path) -> dict:
    """Exact source-authenticated metadata; PNG bytes are read, never published."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow required for offline PNG source observation") from exc
    with zipfile.ZipFile(source_zip) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)) or "source-corpus.json" not in names:
            raise ValueError("missing/ambiguous original source corpus manifest")
        raw=archive.read("source-corpus.json")
        if sha(raw)!=CORPUS_MANIFEST_SHA256:
            raise ValueError("not the exact authenticated original ROM corpus manifest")
        corpus=json.loads(raw)
        if (corpus.get("schema")!=SOURCE_CORPUS_SCHEMA
                or corpus.get("source_rom_sha256")!=ORIGINAL_ROM_SHA256
                or corpus.get("source_rom_verified_and_used_for_composition") is not True
                or corpus.get("unique_rgba_images")!=41
                or corpus.get("unique_binary_silhouettes")!=35
                or corpus.get("unique_representations")!=59):
            raise ValueError("unexpected original source evidence class or counts")
        reps=corpus.get("source_representations")
        if not isinstance(reps,dict) or len(reps)!=59:
            raise ValueError("not all source representations present")
        images={}
        per_mask=defaultdict(set)
        for label,rec in sorted(reps.items()):
            if not isinstance(rec,dict):
                raise ValueError("invalid source representation")
            path=rec.get("local_file")
            if (type(path) is not str or not path.startswith("stock/source-")
                    or not path.endswith(".png") or Path(path).is_absolute()
                    or ".." in Path(path).parts or path not in names):
                raise ValueError("untrusted original source PNG path")
            if path not in images:
                png=archive.read(path)
                if sha(png)!=rec.get("local_png_sha256"):
                    raise ValueError("changed original source PNG bytes")
                with Image.open(io.BytesIO(png)) as image:
                    if image.mode!="RGBA" or image.size!=(64,64):
                        raise ValueError("wrong source image mode or resolution")
                    rgba=image.tobytes()
                if (sha(rgba)!=rec.get("source_rgba_sha256")
                        or sha(rgba[3::4])!=rec.get("source_alpha_sha256")
                        or sha(bytes(a!=0 for a in rgba[3::4]))!=rec.get("source_binary_mask_sha256")):
                    raise ValueError("source image alpha/RGBA differs from authenticated record")
                images[path]=(rec["source_binary_mask_sha256"],rec["source_rgba_sha256"],
                              ring_candidates(rgba))
            mask,original_sha,obs=images[path]
            if (mask!=rec.get("source_binary_mask_sha256")
                    or original_sha!=rec.get("source_rgba_sha256")):
                raise ValueError("source PNG/alpha identity inconsistent across labels")
            per_mask[mask].add(json.dumps(obs,sort_keys=True))
        if len(images)!=41 or len(per_mask)!=35:
            raise ValueError("authenticated unique color/mask identity lost")
        disagreement=sum(len(v)>1 for v in per_mask.values())
        if disagreement:
            raise ValueError("palette variants disagree on neutral-grey wheel centre")
        rows=[{
            "source_rgba_sha256":value[1],
            "source_binary_mask_sha256":value[0],
            "2d_ring_candidate":value[2],
        } for path,value in sorted(images.items())]
        hits=[r["2d_ring_candidate"]["max_neutral_ring_hits"] for r in rows]
        candidate_counts=[len(r["2d_ring_candidate"]["best_candidate_centres_xy_radius_logical_px"])
                          for r in rows]
        radii={c[2] for row in rows for c in
               row["2d_ring_candidate"]["best_candidate_centres_xy_radius_logical_px"]}
        return {
            "schema":SCHEMA,"source_corpus_manifest_sha256":CORPUS_MANIFEST_SHA256,
            "original_usa_rom_sha256":ORIGINAL_ROM_SHA256,
            "source_kind":"authentic ROM-composed authored-reference 2D rasters",
            "unique_rgba_images":41,"unique_binary_silhouettes":35,
            "source_representations_verified":59,
            "palette_duplicate_silhouettes_with_divergent_ring_candidates":disagreement,
            "candidate_radius_logical_px_values":sorted(radii),
            "min_max_neutral_ring_hits":[min(hits),max(hits)],
            "ambiguous_centre_image_count":sum(n>1 for n in candidate_counts),
            "candidate_centre_count_distribution":{
                str(n):candidate_counts.count(n) for n in sorted(set(candidate_counts))
            },
            "images":rows,
            "original_emulator_animation_timing_verified":False,
            "raster_centre_is_not_source_3d_axle":True,
            "rig_camera_and_pose_registered":False,
            "owner_likeness_approved":False,
            "shipping_art_approved":False,
        }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=validate_corpus_and_measure(a.source_zip)
    publish_text_once(a.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({key:value for key,value in result.items() if key!="images"},
                     sort_keys=True,indent=2))


if __name__=="__main__":
    main()
