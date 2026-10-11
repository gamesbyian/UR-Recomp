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
LEDGERS = sorted(p.name for p in (ROOT / "analysis/data").glob("racer-hd-art-approval*.json"))
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
        if ledger["family_blockers"]:\n            continue
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

def load_pair(spec, approved, base):
    key = spec["representation_id"]
    if key not in approved:
        raise ValueError(f"Unapproved representation: {key}")
    stock_path = (base / spec["stock_png"]).resolve()
    authored_path = (base / spec["authored_png"]).resolve()
    stock = Image.open(stock_path).convert("RGBA")
    authored = Image.open(authored_path).convert("RGBA")
    if stock.size != (64,64) or authored.size != (256,256):
        raise ValueError(f"Expected 64x64 stock and 256x256 authored, got {stock.size}, {authored.size}")
    digest = sha(authored.tobytes())
    if digest != approved[key]["digest"]:
        raise ValueError(f"Authored RGBA approval mismatch for {key}: {digest}")
    if not spec.get("stock_source") or not spec.get("stock_evidence"):
        raise ValueError("stock_source and stock_evidence must identify authentic extraction and proof")
    if spec.get("stock_rgba_sha256") and spec["stock_rgba_sha256"] != sha(stock.tobytes()):\n        raise ValueError("Original ROM sprite RGBA checksum mismatch")\n    if stock.getbbox() is None or authored.getbbox() is None:
        raise ValueError("Empty source artwork")
    return stock, authored, {
        **approved[key], "representation_id": key, "guest_frame": spec.get("frame"),
        "stock_png": spec["stock_png"], "stock_file_sha256": sha(stock_path.read_bytes()),
        "stock_rgba_sha256": sha(stock.tobytes()),
        "stock_source": spec["stock_source"], "stock_evidence": spec["stock_evidence"],
        "authored_png": spec["authored_png"],
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
    idx = (tick//8)%len(pairs)
    # Choose evenly spaced timeline entries rather than treating repeated holds as distinct poses.\n    positions = [round(j*(len(pairs)-1)/7) for j in range(8)]\n    for j, pos in enumerate(positions):\n        stock,authored,meta = pairs[pos]\n        left=120+j*210
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
    idx=(tick//8)%n
    stock,art,_=pairs[idx]
    artwork(im,stock,(210,290,560,560),True)
    artwork(im,art,(1100,290,560,560),False)
    d=ImageDraw.Draw(im)
    text(d,(270,875),"SNES SOURCE",32)
    text(d,(1130,875),"AUTHORED 4x",32)
    text(d,(840,555),">",78,"#ef5783")
    return im

def encode(outdir, name, frames, expected):
    # Stream frames to FFmpeg. Never retain 570 1080p PNGs in CI.
    target = outdir / (name+".mp4")
    cmd = ["ffmpeg","-hide_banner","-loglevel","error","-y",
           "-f","rawvideo","-pix_fmt","rgb24","-s","1920x1080",
           "-r",str(FPS),"-i","pipe:0","-an",
           "-c:v","libx264","-preset","veryfast","-crf","17",
           "-pix_fmt","yuv420p","-movflags","+faststart",str(target)]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    samples=[]
    count=0
    try:
        for i,img in enumerate(frames):
            frame=img.convert("RGB")
            process.stdin.write(frame.tobytes())
            if i in {0, expected//4, expected//2, 3*expected//4, expected-1}:
                small=frame.resize((480,270),Image.Resampling.LANCZOS)
                samples.append(small)
            count+=1
        process.stdin.close()
        stderr=process.stderr.read().decode(errors="replace")
        code=process.wait()
        if code or count!=expected:
            raise RuntimeError(f"FFmpeg failed: exit={code} frames={count}/{expected}: {stderr}")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
    sheet=Image.new("RGB",(480*len(samples),270),BG)
    for i,small in enumerate(samples):
        sheet.paste(small,(480*i,0))
    sheet_path=outdir/(name+"-contact-sheet.png")
    sheet.save(sheet_path)
    probe=json.loads(subprocess.check_output([
        "ffprobe","-v","error","-count_frames","-select_streams","v:0",
        "-show_entries","stream=width,height,nb_read_frames,r_frame_rate",
        "-of","json",str(target)]))
    stream=probe["streams"][0]
    if (int(stream["nb_read_frames"])!=expected or
        int(stream["width"])!=1920 or int(stream["height"])!=1080 or
        stream["r_frame_rate"]!="30/1"):
        raise ValueError(f"Incorrect output frame/size/fps {stream}")
    # Decode the whole video, not just the container's frame index.
    subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(target),
                    "-f","null","-"],check=True)
    return {"filename":target.name,"sha256":sha(target.read_bytes()),
            "frames":expected,"fps":FPS,"seconds":expected/FPS,
            "contact_sheet":sheet_path.name,
            "contact_sheet_sha256":sha(sheet_path.read_bytes())}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True,
                   help="JSON with frames [{representation_id,stock_png,authored_png,stock_source,stock_evidence}]")
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if not shutil.which("ffmpeg"):
        raise SystemExit("FFmpeg required")
    spec=json.loads(a.manifest.read_text())
    approved=approvals()\n    pairs=[load_pair(x,approved,a.manifest.resolve().parent) for x in spec["frames"]]
    if len(pairs)<2:
        raise ValueError("Need >=2 verified ordered poses for animation archaeology")
    a.output.mkdir(parents=True,exist_ok=True)
    clips=[\n        encode(a.output,"01-original-4x-remastered",(comparison(*pairs[0][:2],i) for i in range(210)),210),\n        encode(a.output,"02-animation-archaeology",(archaeology(pairs,i) for i in range(210)),210),\n        encode(a.output,"03-remaster-progress",(montage(pairs,i) for i in range(150)),150),\n    ]
    provenance={"schema_version":1,"format":"1920x1080 h264 yuv420p",
                "claim":"Verified art demonstrations. Editorial motion, not native gameplay.",
                "approval_sources":LEDGERS,"assets":[x[2] for x in pairs],"clips":clips}
    (a.output/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
    for clip in clips:
        print(f"{clip['filename']} {clip['frames']} frames {clip['seconds']:.1f}s {clip['sha256']}")

if __name__ == "__main__":
    main()
