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
        if ledger["family_blockers"]:
            continue
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
    if spec.get("stock_rgba_sha256") and spec["stock_rgba_sha256"] != sha(stock.tobytes()):
        raise ValueError("Original ROM sprite RGBA checksum mismatch")
    if stock.getbbox() is None or authored.getbbox() is None:
        raise ValueError("Empty source artwork")
    return stock, authored, {
        **approved[key], "representation_id": key, "guest_frame": spec.get("frame"), "player": spec.get("player"),
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
    # Exact identical crop in source logical coordinates, applied at
    # the source's declared 1x or approved authored 4x density.
    # All frames in the retained first-family motion strip remain inside
    # 12..52 x 0..48; the crop is editorial, never a gameplay admission.
    factor = img.width // 64
    if img.size != (64 * factor, 64 * factor) or factor not in (1,4):
        raise ValueError("Unsupported source/approved art density")
    crop = img.crop((12*factor,0,52*factor,48*factor))
    x,y,w,h = rect
    scale = min(w/crop.width,h/crop.height)
    rendered = crop.resize((round(crop.width*scale),round(crop.height*scale)),
                          Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS)
    canvas.alpha_composite(rendered,(x+(w-rendered.width)//2,y+(h-rendered.height)//2))

def backdrop(name, subtitle):
    im = Image.new("RGBA",SIZE,BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0,0,1920,12),fill="#ef5783")
    d.line((100,190,1820,190), fill="#2b3755",width=2)
    text(d,(110,68),name,62)
    text(d,(112,148),subtitle,27,"#b6c5df")
    text(d,(112,1000),"VERIFIED ART SAMPLE | EDITORIAL MOTION, NOT NATIVE GAMEPLAY",24,"#b6c5df")
    return im

def comparison(stock, authored, tick):
    # Exactly registered crop and pose throughout all three stages.
    stage = min(2,tick//70)
    names = ["01 / ROM PIXELS","02 / EXACT NEAREST 4x","03 / APPROVED AUTHORED 4x"]
    im = backdrop("ONE POSE. THREE PRESENTATIONS.",names[stage])
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((475,214,1445,918),radius=22,
                        outline="#43516f",width=3)
    artwork(im, stock if stage < 2 else authored, (555,224,800,668), stage < 2)
    text(d,(135,315),"64 x 64",40)
    text(d,(135,372),"ROM CANVAS",28,"#91a4c8")
    text(d,(1460,315),"256 x 256",40)
    text(d,(1460,372),"4x CANVAS",28,"#91a4c8")
    if stage == 0:
        text(d,(130,760),"RAW 1x",31,"#ef5783")
        text(d,(130,810),"Nearest-pixel close-up",25)
    elif stage == 1:
        text(d,(130,760),"SAME PIXELS",31,"#ef5783")
        text(d,(130,810),"No newly authored detail",25)
    else:
        text(d,(130,760),"HASH APPROVED",31,"#ef5783")
        text(d,(130,810),"New 4x authored detail",25)
    text(d,(570,937),"Same registered pose, same contact point, exact source pixel coordinates",23)
    return im

def archaeology(pairs, tick):
    im = backdrop("ANIMATION ARCHAEOLOGY","Guest-ordered ROM poses -> extracted frames -> approved 4x reconstruction")
    d = ImageDraw.Draw(im)
    idx = (tick//8)%len(pairs)
    # Show unique byte-distinct poses in the strip; still animate every
    # actual guest timeline frame below, including repeated hold frames.
    positions = []
    seen = set()
    for k, (_,_,meta) in enumerate(pairs):
        digest = meta["stock_rgba_sha256"]
        if digest not in seen:
            positions.append(k)
            seen.add(digest)
    for j,pos in enumerate(positions):
        stock,authored,meta=pairs[pos]
        left=112+round(j*1590/max(1,len(positions)-1))
        current = meta["stock_rgba_sha256"] == pairs[idx][2]["stock_rgba_sha256"]
        d.rounded_rectangle((left,273,left+170,479),radius=10,
                            outline="#ef5783" if current else "#405069",
                            width=4 if current else 2)
        artwork(im,stock,(left+9,286,150,169),True)
        text(d,(left+45,492),str(meta["guest_frame"]),23)
    stock,authored,meta=pairs[idx]
    artwork(im,stock,(285,582,540,355),True)
    artwork(im,authored,(1090,582,540,355),False)
    text(d,(390,941),"EXTRACTED SOURCE",26)
    text(d,(1195,941),"APPROVED 4x",26)
    text(d,(874,693),">",80,"#ef5783")
    label=f"GUEST FRAME {meta['guest_frame']}  |  P1  |  ROM COMPOSITION VERIFIED"
    text(d,(498,555),label,24,"#bacbe3")
    return im

def montage(pairs,tick):
    im = backdrop("RESTORING THE ORIGINAL MOTION","Approved red and blue racers | exact pose and palette identities")
    n=len(pairs)
    idx=(tick//5)%n
    stock,art,meta=pairs[idx]
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((135,235,825,907),radius=20,outline="#405069",width=2)
    d.rounded_rectangle((1095,235,1785,907),radius=20,outline="#405069",width=2)
    artwork(im,stock,(205,275,550,575),True)
    artwork(im,art,(1165,275,550,575),False)
    color = "#ef5783" if meta.get("player")=="p1" else "#5bb8f8"
    label = "P1 / RED" if meta.get("player")=="p1" else "P2 / BLUE"
    text(d,(142,921),f"ROM-EXTRACTED | GUEST {meta['guest_frame']}",26)
    text(d,(1100,921),f"HASH-APPROVED 4x | {label}",26,color)
    text(d,(893,560),">",82,color)
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
    p.add_argument("--secondary-manifest",type=Path,help="Optional approved other-player strip for montage")
    a=p.parse_args()
    if not shutil.which("ffmpeg"):
        raise SystemExit("FFmpeg required")
    spec=json.loads(a.manifest.read_text())
    approved=approvals()
    pairs=[load_pair(x,approved,a.manifest.resolve().parent) for x in spec["frames"]]
    if len(pairs)<2:
        raise ValueError("Need >=2 verified ordered poses for animation archaeology")
    a.output.mkdir(parents=True,exist_ok=True)
    montage_pairs = pairs
    if a.secondary_manifest:
        extra = json.loads(a.secondary_manifest.read_text())
        secondary = [load_pair(x,approved,a.secondary_manifest.resolve().parent) for x in extra["frames"]]
        if len(secondary)!=len(pairs) or not all(x[2].get("player")=="p2" for x in secondary):
            raise ValueError("Secondary strip must be a matching P2 timeline")
        if [x[2]["guest_frame"] for x in secondary] != [x[2]["guest_frame"] for x in pairs]:
            raise ValueError("P1/P2 guest frame order mismatch")
        montage_pairs = [pose for pair in zip(pairs,secondary) for pose in pair]
    clips=
        encode(a.output,"01-original-4x-remastered",(comparison(*pairs[0][:2],i) for i in range(210)),210),
        encode(a.output,"02-animation-archaeology",(archaeology(pairs,i) for i in range(210)),210),
        encode(a.output,"03-remaster-progress",(montage(montage_pairs,i) for i in range(150)),150),
    ]
    provenance={"schema_version":1,"format":"1920x1080 h264 yuv420p",
                "claim":"Verified art demonstrations. Editorial motion, not native gameplay.",
                "approval_sources":LEDGERS,"assets":[x[2] for x in montage_pairs],"clips":clips}
    (a.output/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
    for clip in clips:
        print(f"{clip['filename']} {clip['frames']} frames {clip['seconds']:.1f}s {clip['sha256']}")

if __name__ == "__main__":
    main()
