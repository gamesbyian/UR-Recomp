#!/usr/bin/env python3
"""Authentic-source 34s vertical recruitment companion and illustrated poster.

The first 21 seconds are selected unchanged in source order from the accepted
2026-10-20 vertical graph-paper film. The four ending plates are explicitly
editorial drawings; never generated/altered gameplay.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
import graph_paper_trailer_art_direction as art

ROOT=Path(__file__).resolve().parents[2]
PRIOR=ROOT/"media/showcase/2026-10-20/graphpaper-final/ur-recomp-graphpaper-action-27s-vertical.mp4"
MASTER=ROOT/"media/showcase/2026-10-26/recruitment/ur-recomp-recruit-contributors-95s-1080p.mp4"
LOGO=ROOT/"media/showcase/2026-10-20/graphpaper-source/uniracers_graphpaper_logo.jpg"
TRACK=ROOT/"media/showcase/2026-10-20/graphpaper-source/uniracers_track_unicycle.jpg"
ACTION=ROOT/"media/showcase/2026-10-20/blue-action-final/verified-source-action-ordinal-0570.png"
EXPECTED={
    PRIOR:"5d61045a5f4cf4fa1c305953003bbc7c893e3f304dc65bd5e89097d067a2e8e1",
    MASTER:"0b616efea5192da0c5658e21818e17fd621bb38c94b594425f9c1d47606512a9",
    LOGO:"489b45ccf5d8d6da4d25b34e841ba9dded96814444a5f06c78325ff45be379a9",
    TRACK:"f5948a2af00352c56169c5059e3f24178b0e6e5ef486ced6a85e048f50091032",
}
OUT=ROOT/"media/showcase/2026-10-26/recruitment"
W,H=1080,1920
PAPER=art.PAPER
INK=art.INK
RED=art.RED
SLATE=art.SLATE
GOLD=art.GOLD
FRAMES=[180,180,180,240]
NAMES=["playtest","artists","agent_hours","join"]

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def run(*args):
    print("+"," ".join(map(str,args)),flush=True)
    subprocess.run([str(x) for x in args],check=True)

def ffprobe(file):
    a=subprocess.check_output(["ffprobe","-v","error","-count_frames","-show_streams","-of","json",str(file)])
    return json.loads(a)["streams"]

def txt(d,s,x,y,size=50,color=INK,bold=True,width=960):
    art.label(d,s,(x,y),size,color,bold,max_width=width)

def canvas():
    im=Image.new("RGB",(W,H),PAPER)
    d=ImageDraw.Draw(im)
    for x in range(0,W,24):
        d.line((x,0,x,H),fill=(239,237,231))
    for y in range(0,H,24):
        d.line((0,y,W,y),fill=(239,237,231))
    for x in range(0,W,120):
        d.line((x,0,x,H),fill=(223,222,216))
    for y in range(0,H,120):
        d.line((0,y,W,y),fill=(223,222,216))
    art.ink_overlay(im,LOGO,(60,213,1480,693),(40,48),990)
    art.ink_overlay(im,TRACK,(0,205,1536,495),(0,1660),1080)
    d=ImageDraw.Draw(im)
    d.line((56,414,1024,414),fill=RED,width=4)
    d.line((56,1615,1024,1615),fill=GOLD,width=3)
    txt(d,"UNIRACERS / THE NEXT LAP",(62,444)[0],444,29,RED,width=950)
    return im

def panel(name):
    im=canvas()
    d=ImageDraw.Draw(im)
    if name=="playtest":
        txt(d,"PLAYTEST THE",58,510,79,width=950)
        txt(d,"WINDOWS BUILD",58,604,79,RED,width=950)
        rows=[
            ("01","1P + 2P RACING","Real controllers and real players"),
            ("02","DISPLAY + AUDIO","Full screen / 1080p / 4K"),
            ("03","SAVES + RECORDS","Cold launches and recovery"),
        ]
        for i,(num,head,sub) in enumerate(rows):
            y=777+i*244
            d.rounded_rectangle((56,y,1024,y+208),radius=16,fill=(255,255,251),outline=(143,141,129),width=3)
            txt(d,num,79,y+18,66,RED,width=160)
            txt(d,head,219,y+17,50,width=765)
            txt(d,sub,221,y+100,32,SLATE,False,width=762)
        txt(d,"Independent hardware acceptance is still open.",63,1550,29,RED,width=950)
    elif name=="artists":
        txt(d,"2D + 3D",58,507,93,RED,width=950)
        txt(d,"ARTISTS WANTED",58,613,80,width=950)
        if ACTION.is_file():
            imsrc=Image.open(ACTION).convert("RGB")
            imsrc.thumbnail((947,533),Image.Resampling.LANCZOS)
            y=773
            d.rectangle((55,y,1024,y+550),fill=(42,44,48))
            im.paste(imsrc,(55+(969-imsrc.width)//2,y+(550-imsrc.height)//2))
            d=ImageDraw.Draw(im)
        txt(d,"MODEL. RIG. ANIMATE. COMPOSITE.",64,1374,41,INK,width=950)
        txt(d,"Rebuild the original rounded CGI racers.",64,1442,33,SLATE,False,width=950)
        txt(d,"Current procedural 4x art is NOT approved.",64,1543,26,RED,width=950)
    elif name=="agent_hours":
        txt(d,"CONTRIBUTE",58,507,91,RED,width=950)
        txt(d,"AGENT HOURS",58,617,91,width=950)
        for i,(a,b) in enumerate([("01","PICK A RANKED JOB"),("02","RUN A CODING AGENT"),("03","SUBMIT + REVIEW")]):
            y=788+i*224
            d.rounded_rectangle((54,y,1025,y+188),radius=14,fill=(255,255,251),outline=(143,141,129),width=3)
            txt(d,a,80,y+24,70,RED,width=140)
            txt(d,b,234,y+41,51,width=765)
        txt(d,"One workboard / five hourly generalists",67,1520,31,SLATE,False,width=950)
        txt(d,"Start with AGENTS.md on GitHub",67,1560,29,RED,width=950)
    elif name=="join":
        txt(d,"HELP BRING",60,530,101,width=950)
        txt(d,"THE RACE BACK.",60,646,88,RED,width=950)
        for i,word in enumerate(["PLAYTEST.","CREATE ART.","CONTRIBUTE."]):
            txt(d,word,76,860+i*114,76,width=910)
        d.rounded_rectangle((49,1280,1030,1561),radius=18,fill=(255,255,251),outline=RED,width=4)
        txt(d,"github.com/gamesbyian/",75,1321,49,RED,width=905)
        txt(d,"UR-Recomp",75,1387,58,RED,width=905)
        txt(d,"ianmakesjokes@gmail.com",75,1483,46,INK,width=905)
    else:
        raise ValueError(name)
    return im

def poster():
    im=art.base()
    art.footer(im,TRACK)
    art.header(im,LOGO,"RESTORE THE RACE","PLAYTEST / 2D + 3D ART / AGENT HOURS","OCTOBER 2026 / RECRUITMENT")
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((120,302,1080,836),radius=18,fill=(249,247,238),outline=art.INK,width=4)
    src=Image.open(ACTION).convert("RGB")
    src.thumbnail((920,487),Image.Resampling.LANCZOS)
    im.paste(src,(140+(920-src.width)//2,324+(487-src.height)//2))
    d=ImageDraw.Draw(im)
    txt(d,"GENUINE JUMPS / 2P",160,803,22,RED,width=920)
    txt(d,"THE NEXT LAP",1140,363,76,INK,width=690)
    txt(d,"NEEDS YOU.",1140,464,75,RED,width=690)
    txt(d,"TEST A WINDOWS BUILD",1141,595,35,INK,width=680)
    txt(d,"REBUILD THE RACERS",1141,651,35,INK,width=680)
    txt(d,"DONATE AGENT HOURS",1141,707,35,INK,width=680)
    txt(d,"github.com/gamesbyian/UR-Recomp",1141,789,25,RED,width=660)
    txt(d,"ianmakesjokes@gmail.com",1141,822,25,INK,width=650)
    return im

def encode(input,output,count,still=False):
    command=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y"]
    if still:command+=["-loop","1","-framerate","60"]
    command+=["-i",input,"-an","-frames:v",str(count),
              "-vf","fps=60,scale=1080:1920:flags=lanczos,format=yuv420p",
              "-c:v","libx264","-preset","veryfast","-crf","22",
              "-g","120","-keyint_min","120","-sc_threshold","0",
              "-r","60","-video_track_timescale","15360",output]
    run(*command)

def render(dest):
    for p,correct in EXPECTED.items():
        if not p.is_file() or sha(p)!=correct:
            raise RuntimeError("Source unavailable or SHA differs: "+str(p))
    dest.mkdir(parents=True,exist_ok=True)
    plates=dest/"vertical-cards"
    plates.mkdir(exist_ok=True)
    for name in NAMES:panel(name).save(plates/(name+".png"))
    poster_file=dest/"ur-recomp-targeted-recruitment-poster-1080p.png"
    poster().save(poster_file)
    work=dest/"_vertical_work"
    work.mkdir(exist_ok=True)
    first=work/"00-authentic-film.mp4"
    encode(PRIOR,first,1260)
    pieces=[first]
    for idx,(name,count) in enumerate(zip(NAMES,FRAMES),1):
        out=work/(f"{idx:02d}-{name}.mp4")
        encode(plates/(name+".png"),out,count,True)
        pieces.append(out)
    listing=work/"list.txt"
    listing.write_text("".join(f"file '{p.resolve()}'\n" for p in pieces))
    silent=work/"silent.mp4"
    run("ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
        "-safe","0","-f","concat","-i",listing,"-c:v","copy",silent)
    out=dest/"ur-recomp-recruit-contributors-34s-vertical.mp4"
    run("ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
        "-i",silent,"-i",MASTER,
        "-filter_complex","[1:a]atrim=0:34,asetpts=PTS-STARTPTS,afade=t=out:st=32.5:d=1.5[a]",
        "-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k",
        "-movflags","+faststart",out)
    streams=ffprobe(out)
    v=next(s for s in streams if s["codec_type"]=="video")
    assert (int(v["width"]),int(v["height"]),v["r_frame_rate"],int(v["nb_read_frames"]))==(1080,1920,"60/1",2040),v
    assert any(s["codec_type"]=="audio" for s in streams)
    witnesses={}
    for second in (3,10,16,21,23,26,29,31,33):
        file=dest/f"social-review-{second:02d}s.png"
        run("ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
            "-ss",str(second),"-i",out,"-frames:v","1",file)
        witnesses[file.name]=sha(file)
    record={
        "schema":"UR-TARGETED-SOCIAL-20261026/1",
        "film":out.name,"sha256":sha(out),"fps":60,"frames":2040,"duration_seconds":34,
        "dimensions":[1080,1920],"poster":poster_file.name,"poster_sha256":sha(poster_file),
        "sources":{"original_vertical":sha(PRIOR),"targeted_flagship_score":sha(MASTER),
                   "original_logo":sha(LOGO),"original_track":sha(TRACK)},
        "source_video_first_frames":1260,
        "final_editorial_plates":[{"name":name,"start_seconds":21+sum(FRAMES[:i])/60,
                                   "duration_seconds":FRAMES[i]/60} for i,name in enumerate(NAMES)],
        "decoded_witnesses":witnesses,
        "limitations":["21s of original source film has genuine independently captured native 2P course footage; no newly generated gameplay",
                       "The additional four vertical plates are illustrated recruitment information, not gameplay",
                       "No newly captured current 1P, 4K Modern menus, or final artistically approved 4x racer characters",
                       "This companion requires independent visual, audio and rights screening before public distribution"]
    }
    (dest/"social-provenance.json").write_text(json.dumps(record,indent=2)+"\n")
    for p in work.iterdir():p.unlink()
    work.rmdir()
    print(json.dumps({"output":str(out),"sha256":sha(out),"poster_sha256":sha(poster_file)},indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--outdir",type=Path,default=OUT)
    args=p.parse_args()
    render(args.outdir)
