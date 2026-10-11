#!/usr/bin/env python3
"""Fail-closed art-showcase editor. Requires actual exported stock and authored PNGs.

No sprite images are generated or inferred. The approved image's raw RGBA
hash must match a shipping approval ledger entry before FFmpeg is launched.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
LEDGERS = [
    "racer-hd-art-approval.json",
    "racer-hd-art-approval-057e-0544.json",
    "racer-hd-art-approval-1244-1252.json",
    "racer-hd-art-approval-1230-1239.json",
    "racer-hd-art-approval-1261-1267.json",
]
FPS = 30
SIZE = (1920, 1080)
BG = "#101525"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def approvals():
    result = {}
    for name in LEDGERS:
        path = ROOT / "analysis/data" / name
        ledger = json.loads(path.read_text())
        assert not ledger["family_blockers"], name
        for d in ledger["decisions"]:
            if not (d["shipping_art_approved"] and d["status"] == "approved" and not d["blocker_codes"]):
                continue
            key = d["authored_source_representation_id"]
            digest = d["reviewed_authored_rgba_sha256"]
            if key in result and result[key]["digest"] != digest:
                raise ValueError(f"Conflicting approved digest: {key}")
            result[key] = {"digest": digest, "ledger": name,
                           "run": ledger["review_basis"]["workflow_run"],
                           "artifact": ledger["review_basis"]["artifact_id"]}
    return result

def load_pair(spec, approved):
    key = spec["representation_id"]
    if key not in approved:
        raise ValueError(f"Unapproved representation: {key}")
    stock_path = Path(spec["stock_png"]).resolve()
    authored_path = Path(spec["authored_png"]).resolve()
    stock = Image.open(stock_path).convert("RGBA")
    authored = Image.open(authored_path).convert("RGBA")
    if stock.size != (64,64) or authored.size != (256,256):
        raise ValueError(f"Expected 64x64 stock and 256x256 authored, got {stock.size}, {authored.size}")
    digest = sha(authored.tobytes())
    if digest != approved[key]["digest"]:
        raise ValueError(f"Authored RGBA approval mismatch for {key}: {digest}")
    if not spec.get("stock_source") or not spec.get("stock_evidence"):
        raise ValueError("stock_source and stock_evidence must identify authentic extraction and proof")
    if stock.getbbox() is None or authored.getbbox() is None:
        raise ValueError("Empty source artwork")
    return stock, authored, {
        **approved[key], "representation_id": key,
        "stock_png": str(stock_path), "stock_file_sha256": sha(stock_path.read_bytes()),
        "stock_rgba_sha256": sha(stock.tobytes()),
        "stock_source": spec["stock_source"], "stock_evidence": spec["stock_evidence"],
        "authored_png": str(authored_path),
        "authored_file_sha256": sha(authored_path.read_bytes()),
        "authored_rgba_sha256": digest,
    }

def font(n):
    paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, n)
    return ImageFont.load_default()

def text(d, xy, content, size=42, color="#edf2ff"):
    d.text(xy, content, font=font(size), fill=color)

def artwork(canvas, img, rect, nearest):
    x,y,w,h = rect
    scale = min(w/img.width, h/img.height)
    rendered = img.resize((round(img.width*scale),round(img.height*scale)),
                          Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS)
    canvas.alpha_composite(rendered,(x+(w-rendered.width)//2,y+(h-rendered.height)//2))

def backdrop(name, subtitle):
    im = Image.new("RGBA",SIZE,BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0,0,1920,12),fill="#ef5783")
    text(d,(110,68),name,62)
    text(d,(112,148),subtitle,27,"#b6c5df")
    text(d,(112,1000),"VERIFIED ART SAMPLE | NOT CONTINUOUS NATIVE GAMEPLAY",24,"#b6c5df")
    return im

def comparison(stock, authored, tick):
    # 210 frames = seven seconds. Original -> registered nearest-4x -> authored 4x.
    stage = min(2,tick//70)
    names = ["ORIGINAL ROM SPRITE","EXACT 4x NEAREST","APPROVED REMASTERED POSE"]
    im = backdrop("ONE POSE. THREE PRESENTATIONS.",names[stage])
    d = ImageDraw.Draw(im)
    large = (660,240,600,600)
    artwork(im, stock if stage < 2 else authored, large, stage < 2)
    if stage == 0:
        # Retain a visible pixel grid only during the source-pixel close-up.
        for z in range(65):
            x=660+z*600//64
            y=240+z*600//64
            d.line((x,240,x,840),fill=(180,190,220,36),width=1)
            d.line((660,y,1260,y),fill=(180,190,220,36),width=1)
    text(d,(690,890),"64 x 64 source  /  256 x 256 approved RGBA",25)
    return im

def archaeology(pairs, tick):
    im = backdrop("ANIMATION ARCHAEOLOGY","ROM-derived ordered poses | editorial playback")
    d = ImageDraw.Draw(im)
    idx = (tick//10)%len(pairs)
    for j, (stock,authored,_) in enumerate(pairs[:8]):
        left=120+j*210
        d.rectangle((left,295,left+190,490),outline="#405069",width=2)
        artwork(im,stock,(left+15,310,160,160),True)
        text(d,(left+65,510),f"{j+1:02d}",25)
    artwork(im,pairs[idx][0],(580,610,300,300),True)
    artwork(im,pairs[idx][1],(1080,610,300,300),False)
    text(d,(630,930),"EXTRACTED",26)
    text(d,(1110,930),"APPROVED 4x",26)
    return im

def montage(pairs,tick):
    im = backdrop("RESTORING THE ORIGINAL MOTION","Hash-approved poses | density and palette are distinct")
    n=len(pairs)
    idx=(tick//18)%n
    stock,art,_=pairs[idx]
    artwork(im,stock,(210,290,560,560),True)
    artwork(im,art,(1100,290,560,560),False)
    d=ImageDraw.Draw(im)
    text(d,(270,875),"SNES SOURCE",32)
    text(d,(1130,875),"AUTHORED 4x",32)
    text(d,(840,555),">",78,"#ef5783")
    return im

def encode(outdir,name,frames):
    temp=outdir/(name+"-frames")
    temp.mkdir(parents=True,exist_ok=True)
    for i,img in enumerate(frames):
        img.convert("RGB").save(temp/f"{i:05d}.png")
    target=outdir/(name+".mp4")
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                    "-framerate",str(FPS),"-i",str(temp/"%05d.png"),
                    "-c:v","libx264","-preset","medium","-crf","17",
                    "-pix_fmt","yuv420p","-movflags","+faststart",str(target)],check=True)
    return {"filename":target.name,"sha256":sha(target.read_bytes()),
            "frames":len(frames),"fps":FPS,"seconds":len(frames)/FPS,
            "source_frame_dir":temp.name}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True,
                   help="JSON with frames [{representation_id,stock_png,authored_png,stock_source,stock_evidence}]")
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if not shutil.which("ffmpeg"):
        raise SystemExit("FFmpeg required")
    spec=json.loads(a.manifest.read_text())
    pairs=[load_pair(x,approvals()) for x in spec["frames"]]
    if len(pairs)<2:
        raise ValueError("Need >=2 verified ordered poses for animation archaeology")
    a.output.mkdir(parents=True,exist_ok=True)
    clips=[
        encode(a.output,"01-original-4x-remastered",(comparison(*pairs[0][:2],i) for i in range(210))),
        encode(a.output,"02-animation-archaeology",(archaeology(pairs,i) for i in range(210))),
        encode(a.output,"03-remaster-progress",(montage(pairs,i) for i in range(150))),
    ]
    provenance={"schema_version":1,"format":"1920x1080 h264 yuv420p",
                "claim":"Verified art demonstrations. Editorial motion, not native gameplay.",
                "approval_sources":LEDGERS,"assets":[x[2] for x in pairs],"clips":clips}
    (a.output/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
    for clip in clips:
        print(f"{clip['filename']} {clip['frames']} frames {clip['seconds']:.1f}s {clip['sha256']}")

if __name__ == "__main__":
    main()
