#!/usr/bin/env python3
"""Rebuild the accepted 80/27s action trailer with the graph-paper card family.

Reuses the exact gameplay/technical source SHA and contiguous-frame checks in
build_flagship_recruitment_20261019.py. No new or fabricated gameplay footage.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import graph_paper_trailer_art_direction as art
import build_flagship_recruitment_20261019 as film

ROOT=Path(__file__).resolve().parents[2]
ART_DIR=ROOT/"media/showcase/2026-10-20/graphpaper-source"
LOGO=ART_DIR/"uniracers_graphpaper_logo.jpg"
TRACK=ART_DIR/"uniracers_footer_long.png"
NAMING={
"ur-recomp-blue-action-80s-1080p.mp4":"ur-recomp-graphpaper-action-80s-1080p.mp4",
"ur-recomp-blue-action-27s-vertical.mp4":"ur-recomp-graphpaper-action-27s-vertical.mp4",
"ur-recomp-blue-action-poster.png":"ur-recomp-graphpaper-action-poster.png",
}
def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()
def render(out, cards_only=False):
    assert LOGO.is_file(), "Original hand-inked logo source is required"
    assert TRACK.is_file(), ("Owner supplied 2026-10-20 long footer missing: " + str(TRACK) + ". Do not silently substitute the obsolete hand-drawn extension.")
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    if cards_only:
        art.produce(out,LOGO,TRACK)
        return
    # Existing parent source/audit logic retains all source SHA and frames.
    # Replace only the card generator; neither guest nor action/video inputs.
    original_generator=film.produce_blue_assets
    old_argv=sys.argv
    film.produce_blue_assets=lambda destination: art.produce(destination,LOGO,TRACK)
    sys.argv=["build_flagship_recruitment_20261019.py","--outdir",str(out)]
    try:
        film.main()
    finally:
        sys.argv=old_argv
        film.produce_blue_assets=original_generator
    manifest_path=out/"flagship-provenance.json"
    manifest=json.loads(manifest_path.read_text())
    for previous,following in NAMING.items():
        (out/previous).rename(out/following)
    # Preserve original gameplay pixels on poster. Only editorial title bands
    # are swapped from the blue treatment to cream sketch-paper.
    p=out/NAMING["ur-recomp-blue-action-poster.png"]
    im=Image.open(p).convert("RGB")
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,1919,93),fill=art.PAPER)
    d.rectangle((0,985,1919,1079),fill=art.PAPER)
    font=ImageFont.truetype(art.BOLD,43)
    d.text((98,16),"UNIRACERS  /  NATIVE WIDESCREEN",fill=art.INK,font=font)
    font=ImageFont.truetype(art.BOLD,31)
    d.text((105,1004),"JUMPS COURSE  /  GENUINE CAPTURE",fill=art.RED,font=font)
    im.save(p)
    manifest["build_edition"]="2026-10-20 graph-paper illustrated recruitment"
    manifest["editorial_art_sources"]={
      "logo":{"path":str(LOGO.relative_to(ROOT)),"sha256":sha(LOGO)},
      "track":{"path":str(TRACK.relative_to(ROOT)),"sha256":sha(TRACK)},
      "renderer":"tools/showcase/graph_paper_trailer_art_direction.py",
      "inset_px":[400,270,1120,630],
      "original_artwork_preserved":True,
      "footer_policy":"new owner supplied continuous track, original aspect ratio, crop top/bottom whitespace only, edge-to-edge",
    }
    manifest["output_sha256"]={
      name:sha(out/name) for name in NAMING.values()
    }
    manifest["claims_and_exclusions"]["visual_redesign"]="Graph-paper sketch editorial 12-card family: original supplied logo and track/wheel drawings"
    manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    for p in (out/n for n in NAMING.values()):
        assert p.is_file() and p.stat().st_size>10000
    print(json.dumps(manifest["output_sha256"],indent=2))
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--outdir",type=Path,required=True)
    parser.add_argument("--cards-only",action="store_true")
    args=parser.parse_args()
    render(args.outdir,args.cards_only)