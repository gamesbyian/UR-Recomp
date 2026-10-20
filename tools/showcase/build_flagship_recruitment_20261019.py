#!/usr/bin/env python3
"""Produce the October 2026 flagship UR-Recomp film from exact, verified captures.

Native footage and editorial visualization are always labelled separately.
A 2026-10-10 Modern capture is never portrayed as a 2026-10-19 playthrough.
No guest rerun, temporal interpolation, fabricated geometry or commercial score.
"""
import argparse
import hashlib
import json
import math
import random
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageStat
from blue_trailer_art_direction import produce as produce_blue_assets

ROOT = Path(__file__).resolve().parents[2]
RECRUIT = ROOT / "media/showcase/2026-10-10/recruitment"
TECH = ROOT / "media/showcase/2026-10-10/technical-motion"
ART = ROOT / "media/showcase/art-reconstruction/2026-10-10"

SOURCES = {
    "title": (RECRUIT/"native-menu/ur-native-title-menu-900f.mp4", "d58e0b0e20226981767dc1c33e0f34d9652e8ecdb6aa97bd914f7d6ddf0f61d3", 900, 60, "genuine_2026_10_10_native"),
    "reveal": (RECRUIT/"presentation-edits/authentic-widescreen-reveal-7s.mp4", "92ea56611a18ee001ae101f36bc0f2600dc9ca117581edd8072df9535f831414", 420, 60, "source_locked_presentation_edit"),
    "action": (ROOT/"media/showcase/2026-10-19/dynamic-native-2p/native-dynamic-2p-three-courses-15s.mp4", "46b5bf43bcfb4f8bdd4874e7a9994f70996688c2c86a259bef01d5102630598d", 900, 60, "genuine_three_distinct_original_native_sessions_with_editorial_cuts"),
    "modern": (RECRUIT/"modern-root/ur-modern-root-600f.mp4", "e43b1c8b9461e94ac2380d164d850545742c958c0dfef98c99987e40197de7db", 600, 60, "genuine_2026_10_10_native"),
    "code": (TECH/"04-machine-code-to-native.mp4", "c213ab1aa5472cb1940d5e35a5601bd30d9c00a9acb1e79cdf6dd1baca5e343d", 270, 30, "editorial_source_qualified"),
    "raster": (TECH/"03-source-raster-xray.mp4", "b818ad56f8da43e6db94b75561373bc3caf258b516abaca81d6ce8ac14285d5b", 180, 30, "editorial_real_raster_crops"),
    "parity": (TECH/"01-source-centre-parity.mp4", "7ebe9163aec9e2c0ab350cf7f402cf3b653202f14a1c544424c5ed879e48b4c6", 180, 30, "editorial_bounded_QA08"),
    "art": (ART/"01-original-4x-remastered.mp4", "0ae94aaa407979ec749bef17d245331c7d8d3595d8a76347b2644f655924bfe4", 210, 30, "editorial_experimental_art"),
    "animation": (ART/"02-animation-archaeology.mp4", "c1326b641eb119375bc7708a6780ce7950be81b7f287d4b010c0c11328750e2a", 210, 30, "editorial_experimental_art"),
    "art_p2": (ART/"03-remaster-progress.mp4", "27731d18bb7197848d082f97eaf6d9393f16996a774dcb80b2c0ae6a67252d52", 150, 30, "editorial_experimental_art"),
}
PAST_POSTER = (RECRUIT/"definitive-film/ur-recomp-recruitment-final-poster.png",
               "d9bcbda5335a2656f81c79607be1fd540ca7403acba403111ad12f4b4270189a")
# Index is a source video or 'card_' editorial graphics. Native time ranges
# are half-open integer frame ordinals, exactly preserving the source cadence.
FILM = [
    ("title", 270, 90, "THE ORIGINAL / 1994", "capture"),
    ("title", 420, 90, "AUTHENTIC ORIGINAL GAME MENU", "capture"),
    ("reveal", 0, 420, "43 NEW WORLD COLUMNS PER SIDE", "editing"),
    ("action", 0, 300, "MEGAJUMP  /  REAL 342-COLUMN TWO-PLAYER RACING", "capture"),
    ("card_windows", 0, 300, "SCRIPTED WIN32 JOURNEYS  /  OCT 19 EVIDENCE", "editorial"),
    ("code", 0, 270, "VERIFIED 65816 MAINLOOP → GENERATED C", "editorial"),
    ("raster", 0, 180, "SOURCE RASTER ARCHAEOLOGY", "editorial"),
    ("parity", 0, 180, "0 / 57,344 SOURCE CENTRE PIXELS DIFFER", "editorial"),
    ("card_4k", 0, 300, "ACTUAL 3840 × 2160 FRAMEBUFFER WITNESS", "editorial"),
    ("art", 0, 150, "EXPERIMENTAL 4× CHARACTER RECONSTRUCTION", "editorial"),
    ("animation", 0, 150, "ANIMATION ARCHAEOLOGY / SOURCE POSES", "editorial"),
    ("art_p2", 0, 150, "PROCEDURAL 4× STUDIES / LIKENESS NOT APPROVED", "editorial"),
    ("action", 300, 300, "JUMPS  /  INVERTED AIRBORNE RIDER", "capture"),
    ("action", 600, 300, "LOOPER  /  ROLLING TRACK, NOT CERTIFIED FULL LOOP", "capture"),
    ("card_cta", 0, 540, "HELP BUILD THE NEXT VERSION", "editorial"),
]
# 27-second portrait short, gameplay fitted rather than cutting either 2P band.
SHORT = [
    ("title", 270, 90, "THE ORIGINAL / 1994", "capture"),
    ("title", 420, 30, "AUTHENTIC CHECKERBOARD MENU", "capture"),
    ("reveal", 0, 420, "THE WORLD OPENS / ORIGINAL WIDE", "editing"),
    ("code", 0, 120, "65816 → NATIVE C / VERIFIED SOURCE", "editorial"),
    ("action", 0, 300, "MEGAJUMP  /  SEPARATED RACERS", "capture"),
    ("action", 300, 300, "JUMPS  /  ACTUAL AIRBORNE RIDER", "capture"),
    ("card_cta", 0, 240, "JOIN THE REBUILD", "editorial"),
]
FPS = 60
INK = (8, 16, 31)
LIGHT = (236, 246, 249)
CYAN = (72, 232, 216)
GOLD = (250, 194, 99)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def digest(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def run(*cmd):
    subprocess.run([str(x) for x in cmd],check=True)

def probe(p):
    x=json.loads(subprocess.check_output(["ffprobe","-v","error","-count_frames",
      "-select_streams","v:0","-show_entries","stream=width,height,r_frame_rate,nb_read_frames",
      "-of","json",str(p)]))["streams"]
    if len(x)!=1:raise ValueError("Must have one video stream: "+str(p))
    return x[0]

def font(size,bold=False):
    return ImageFont.truetype(BOLD if bold else FONT,size)

def text_fit(d,point,message,size,fill=LIGHT,bold=False,width=1580):
    while size>18 and d.textbbox((0,0),message,font=font(size,bold))[2]>width:
        size-=2
    d.text(point,message,font=font(size,bold),fill=fill)
    return size

def background():
    im=Image.new("RGB",(1920,1080),INK)
    d=ImageDraw.Draw(im)
    # Precise technical diagrams, deliberately editorial rather than game assets.
    for x in range(0,1920,80):d.line((x,0,x,1080),fill=(14,31,49),width=1)
    for y in range(0,1080,80):d.line((0,y,1920,y),fill=(14,31,49),width=1)
    d.rectangle((0,0,1919,8),fill=CYAN)
    d.rectangle((110,161,118,902),fill=GOLD)
    d.line((115,962,1806,962),fill=(53,111,129),width=3)
    text_fit(d,(132,978),"UR-RECOMP    /    INDEPENDENT EVIDENCE • OCTOBER 2026",24,(161,185,207))
    return im,d

def make_cards(folder):
    cards={}
    im,d=background()
    text_fit(d,(145,85),"NATIVE WINDOWS PRODUCT",32,CYAN,True)
    text_fit(d,(145,200),"FROM ZERO TO A SAVED RECORD",77,LIGHT,True)
    tasks=[("01","CREATE RACER","Named-profile native onboarding"),
           ("02","COMPLETE NATIVE RACE","Scripted 1P / 2P result journeys"),
           ("03","REOPEN RECORDS","Cold process restart, canonical entries")]
    for i,(number,head,sub) in enumerate(tasks):
        x=150+i*559
        d.rounded_rectangle((x,385,x+529,751),radius=22,fill=(17,41,65),outline=(56,130,150),width=3)
        text_fit(d,(x+28,405),number,62,GOLD,True)
        text_fit(d,(x+28,530),head,35,LIGHT,True,width=480)
        text_fit(d,(x+28,620),sub,22,(182,204,219),width=470)
        if i<2:d.polygon([(x+529,540),(x+546,554),(x+529,568)],fill=CYAN)
    text_fit(d,(148,832),"Verified scripted native Windows journeys. Physical controller and release QA remain open.",25,(183,206,226),width=1670)
    cards["card_windows"]=folder/"editorial-windows-evidence.png";im.save(cards["card_windows"])
    im,d=background()
    text_fit(d,(145,78),"ACTUAL SDL FRAMEBUFFER • BOUNDED ORIGINAL 2P",30,CYAN,True)
    text_fit(d,(145,205),"8,294,400",158,GOLD,True)
    text_fit(d,(153,414),"SOURCE-CHECKED OUTPUT PIXELS",65,LIGHT,True)
    text_fit(d,(150,574),"3840 × 2160   /   FRAME 2208   /   7:6 ORIGINAL PIXEL ASPECT",32,(183,219,226),True)
    for i,v in enumerate(["342×224 genuine logical world","4× nearest Original compositor","Exact SDL output readback"]):
        y=680+i*75
        d.rounded_rectangle((152,y,1725,y+61),radius=14,fill=(17,40,61),outline=(38,93,115),width=2)
        text_fit(d,(178,y+12),v,31,LIGHT)
    text_fit(d,(145,924),"This card cites real output QA, NOT newly filmed 4K gameplay.",22,GOLD,True)
    cards["card_4k"]=folder/"editorial-4k-evidence.png";im.save(cards["card_4k"])
    im,d=background()
    text_fit(d,(145,88),"ONE GENUINE GAME. A MUCH BIGGER PROJECT.",30,CYAN,True)
    text_fit(d,(142,230),"UNIRACERS",125,LIGHT,True)
    text_fit(d,(148,372),"NATIVE RECOMP",85,GOLD,True)
    text_fit(d,(148,520),"BUILD THE NEXT VERSION",73,LIGHT,True)
    skills=["C++ / REVERSE ENGINEERING","3D CHARACTER ART / ANIMATION","SOURCE-GROUNDED QA / TOOLING"]
    for i,v in enumerate(skills):
        text_fit(d,(166,656+i*64),"• "+v,32,CYAN,True)
    d.rounded_rectangle((140,880,1782,956),radius=20,fill=(29,98,113),outline=CYAN,width=2)
    text_fit(d,(206,896),"github.com/gamesbyian/UR-Recomp",44,LIGHT,True)
    cards["card_cta"]=folder/"editorial-contribution-invitation.png";im.save(cards["card_cta"])
    return cards

def render_score(path,seconds=85,rate=22050):
    """Newly synthesized, deterministic 132 BPM electronic score. No samples."""
    progression=[(174.61,261.63,349.23),(138.59,207.65,277.18),
                 (207.65,311.13,415.30),(155.56,233.08,311.13)]
    rng=random.Random(1205)
    bpm=132
    beat=60/bpm
    with wave.open(str(path),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate)
        buf=bytearray()
        for i in range(seconds*rate):
            t=i/rate; k=int(t/beat)
            chord=progression[(k//8)%4]
            phase=t%beat
            kick=math.sin(2*math.pi*(58*phase+0.18*(1-math.exp(-30*phase))))*0.21*math.exp(-10*phase)
            hat=((rng.random()*2-1)*0.06*math.exp(-27*(t%(beat/2))))
            snare=(rng.random()*2-1)*0.09*math.exp(-18*((t+beat/2)%beat)) if k%2 else 0
            bassphase=(t*chord[0]/2)%1
            bass=(2*abs(2*bassphase-1)-1)*0.17
            arpfreq=chord[(k*2+int(t/(beat/2)))%3]
            arp=math.sin(2*math.pi*arpfreq*t)*0.08*math.exp(-5*(t%(beat/2)))
            pad=sum(math.sin(2*math.pi*frequency*t)*0.02 for frequency in chord)
            energy=0.80 if t<4 else (0.95 if t<38 else (0.89 if t<70 else 1.0))
            fade=min(1,t/0.6,max(0,(seconds-t)/2))
            out=max(-.85,min(.85,(kick+hat+snare+bass+arp+pad)*energy*fade))
            buf.extend(int(out*32767).to_bytes(2,"little",signed=True))
            if len(buf)>=32768:f.writeframesraw(buf);buf.clear()
        if buf:f.writeframesraw(buf)

def make_segment(src,start,frames,source_fps,caption,kind,output,vertical=False,blue_frame=None):
    dur=frames/source_fps
    if vertical:
        width,height=1080,1920
        # Pixel-perfect entire 2P raster fitted at correct aspect.
        visual=("scale=1080:608:flags=neighbor,"
                "pad=1080:1920:0:656:0x08101f")
        cap=caption.replace("'","").replace(":"," ").replace("→","TO")
        cap=cap[:48]
        stamp=(
          ",drawtext=text='"+cap+"':fontsize=35:fontcolor=white:"
          "x=(w-text_w)/2:y=450:box=1:boxcolor=black@0.62:boxborderw=14")
    else:
        width,height=1920,1080
        visual="scale=1707:960:flags=neighbor,pad=1920:1080:106:60:0x08101f"
        cap=caption.replace("'","").replace(":"," ").replace("→","TO")[:78]
        stamp=(
           ",drawtext=text='"+cap+"':fontsize=25:fontcolor=white:"
           "x=120:y=13,"
           "drawtext=text='"+("EDITORIAL" if kind=="editorial" else "SOURCE / AUTHENTIC VIDEO")+
           "':fontsize=18:fontcolor=0x48e8d8:x=w-text_w-120:y=18")
    if src is None:
        raise ValueError("Missing source for editorial card")
    fade="fade=t=in:st=0:d=0.10,fade=t=out:st="+str(max(0,dur-0.12))+":d=0.12"
    vf="fps=60,"+visual+stamp+","+fade+",format=yuv420p"
    if blue_frame and not vertical:
        filter_graph=(
            "[0:v]fps=60,scale=1120:630:flags=neighbor,format=rgba[clip];"
            "[1:v]format=rgba[design];"
            "[design][clip]overlay=x=400:y=270:shortest=1,"
            +fade+",format=yuv420p[final]")
        run("ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
            "-loop","1","-framerate","60","-i",blue_frame,
            "-ss",str(start/source_fps),"-i",src,
            "-t",str(dur),"-filter_complex",
            "[1:v]fps=60,scale=1120:630:flags=neighbor,format=rgba[clip];"
            "[0:v]format=rgba[design];"
            "[design][clip]overlay=x=400:y=270:shortest=1,"
            +fade+",format=yuv420p[final]",
            "-map","[final]","-an","-frames:v",str(round(dur*FPS)),
            "-r","60","-c:v","libx264","-preset","ultrafast","-crf","20",
            "-pix_fmt","yuv420p","-video_track_timescale","60000",output)
        o=probe(output)
        assert (o["width"],o["height"],o["r_frame_rate"],int(o["nb_read_frames"]))==(
            1920,1080,"60/1",round(dur*FPS)),(output,o)
        return
    run("ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
        "-ss",str(start/source_fps),"-i",src,
        "-t",str(dur),"-vf",vf,"-an","-frames:v",str(round(dur*FPS)),
        "-r",str(FPS),"-c:v","libx264","-preset","ultrafast","-crf","21",
        "-g","60","-pix_fmt","yuv420p","-video_track_timescale","60000",output)
    o=probe(output)
    assert (o["width"],o["height"],o["r_frame_rate"],int(o["nb_read_frames"]))==(
        width,height,"60/1",round(dur*FPS)), (output,o)

def make_film(shots,sources,cards,target,score,tmp,vertical=False):
    tmp.mkdir(parents=True,exist_ok=True)
    parts=[]
    total=0
    for i,(key,start,frames,caption,kind) in enumerate(shots):
        source_fps=60
        if key.startswith("card_"):
            input_path=cards[key]
            source_fps=60
            # loop still with source exactly lasting the specified frame count
            duration=frames/FPS
            part=tmp/f"part-{i:02d}.mp4"
            cap=caption.replace("'","").replace(":"," ").replace("→","TO")[:65]
            vis=("scale=1080:608:flags=neighbor,pad=1080:1920:0:656:0x08101f"
                 if vertical else "scale=1920:1080:flags=neighbor")
            textline=(",drawtext=text='"+cap+"':fontsize=36:fontcolor=white:"
                      "x=(w-text_w)/2:y=440" if vertical else "")
            run("ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                "-loop","1","-framerate","60","-i",input_path,"-t",str(duration),
                "-vf",vis+textline+",fade=t=in:st=0:d=0.16,"
                      "fade=t=out:st="+str(max(0,duration-0.18))+":d=0.18,format=yuv420p",
                "-an","-frames:v",str(frames),"-r","60","-c:v","libx264",
                "-preset","ultrafast","-crf","21","-g","60","-pix_fmt","yuv420p",
                "-video_track_timescale","60000",part)
        else:
            input_path,_,_,source_fps,_=sources[key]
            part=tmp/f"part-{i:02d}.mp4"
            make_segment(input_path,start,frames,source_fps,caption,kind,part,vertical,
                blue_frame=(cards["__artdir__"] / (key+"-frame.png")
                if not vertical and key in ("reveal","code","raster","parity","art","animation","art_p2") else None))
        parts.append(part)
        total+=round(frames/source_fps*FPS)
    expected=27 if vertical else 80
    assert total==expected*FPS,(total,expected)
    listing=tmp/"concat.txt"
    listing.write_text("".join("file '"+str(p.resolve())+"'\n" for p in parts))
    # Uniform encoded source pads and frame cadence. Re-encode once to ensure
    # correct timestamps, then mux only our own score. No motion interpolation.
    run("ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
        "-f","concat","-safe","0","-i",listing,"-i",score,
        "-map","0:v:0","-map","1:a:0","-frames:v",str(total),
        "-t",str(expected),"-c:v","libx264","-preset","veryfast","-crf","19",
        "-pix_fmt","yuv420p","-r","60","-c:a","aac","-b:a","160k",
        "-movflags","+faststart",target)
    width,height=(1080,1920) if vertical else (1920,1080)
    got=probe(target)
    assert (got["width"],got["height"],got["r_frame_rate"],int(got["nb_read_frames"]))==(
        width,height,"60/1",expected*60),(target,got)
    return total

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--outdir",type=Path,required=True)
    a=parser.parse_args()
    a.outdir.mkdir(parents=True,exist_ok=True)
    for key,(path,expected,frames,fps,classification) in SOURCES.items():
        assert digest(path)==expected,(key,"source checksum mismatch")
        p=probe(path)
        assert (p["width"],p["height"],p["r_frame_rate"],int(p["nb_read_frames"]))==(1920,1080,f"{fps}/1",frames),(key,p)
    # Historical poster only for documentation; new edition uses source Jumps frame.
    # A source-derived poster remains an original-game recording, not a
    # fabricated Remastered gameplay still.
    with tempfile.TemporaryDirectory(prefix="ur-flagship-") as t:
        tmp=Path(t)
        produce_blue_assets(tmp / "blue-art")
        cards={k:tmp/"blue-art"/(k.removeprefix("card_")+".png") for k in ("card_windows","card_4k","card_cta")}
        cards["__artdir__"]=tmp/"blue-art"
        score=tmp/"original-flagship-score.wav"
        render_score(score)
        master=a.outdir/"ur-recomp-blue-action-80s-1080p.mp4"
        vertical=a.outdir/"ur-recomp-blue-action-27s-vertical.mp4"
        make_film(FILM,SOURCES,cards,master,score,tmp/"film")
        make_film(SHORT,SOURCES,cards,vertical,score,tmp/"short",vertical=True)
        # Genuine Jumps track/racer frame (source ordinal 570 in the verified
        # 900-frame three-course reel), never an invented promotional scene.
        still=tmp/"verified-jumps-gameplay-still.png"
        run("ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
            "-i",SOURCES["action"][0],"-vf","select=eq(n\\\\,570)",
            "-vsync","vfr","-frames:v","1",still)
        im=Image.open(still).convert("RGB")
        d=ImageDraw.Draw(im)
        d.rectangle((0,0,1920,93),fill=INK)
        d.rectangle((0,985,1920,1080),fill=INK)
        text_fit(d,(102,14),"UNIRACERS RECOMP  /  NATIVE WIDESCREEN",46,YELLOW,True)
        text_fit(d,(108,1007),"JUMPS COURSE  •  AUTHENTIC GAMEPLAY FRAME",32,CREAM,True)
        poster=a.outdir/"ur-recomp-blue-action-poster.png";im.save(poster)
    claims={
        "release_status":"NOT A FINISHED BETA",
        "independently_accepted_USA_events":"0/45 as of 2026-10-19",
        "windows_release_QA_gates":"0/12 as of 2026-10-19",
        "source_gameplay_segments":"uninterpolated, source-contiguous per individual segment",
        "original_wide":"342x224 with 43 real additional source columns per side",
        "action_reel":"Three separately captured authentic guest runs of MegaJump, Jumps, Looper, each 300 consecutive frames; editorial cuts and separate race sessions clearly identified",
        "loop_claim":"Looper shows graded rolling geometry; no complete loop revolution confirmed",
        "airborne_claim":"Jumps has independently reviewed inverted airborne rider source ordinal 570",
        "modern_footage":"The obsolete October 10 temporary Modern menu video is excluded from this edition",
        "windows_journey_card":"editorial recap of scripted Win32 result/profile/Records evidence; not live footage",
        "full_SDL_4k_card":"bounded 2026-10-10 real 3840x2160 SDL pixel readback for Original-mode frame 2208; not 4k video",
        "art_demo":"procedural 4x prototypes under October 10 visual likeness veto, never finished approved character designs",
        "technical_65816_C":"same genuine MainLoop opcode and pinned generated C; no whole-game execution parity claim",
        "soundtrack":"new deterministic original synth, no sampled copyrighted music"
    }
    outputs=[master,vertical,poster]
    manifest={
        "schema":"UR-FLAGSHIP-RECRUITMENT/1",
        "build_edition":"2026-10-19",
        "source_identity":{k:{"path":str(v[0].relative_to(ROOT)),"sha256":v[1],"frames":v[2],"fps":v[3],"classification":v[4]} for k,v in SOURCES.items()},
        "poster_source":{"path":str(SOURCES["action"][0].relative_to(ROOT)),"sha256":SOURCES["action"][1],"source_ordinal":570,"actual_inverted_airborne_rider_source":True},
        "horizontal_shots":[{"source":k,"source_first_ordinal":start,"source_frame_count":n,
          "label":label,"classification":kind} for k,start,n,label,kind in FILM],
        "vertical_shots":[{"source":k,"source_first_ordinal":start,"source_frame_count":n,
          "label":label,"classification":kind} for k,start,n,label,kind in SHORT],
        "output_sha256":{p.name:digest(p) for p in outputs},
        "claims_and_exclusions":claims,
        "total_horizontal_frames":4800,"total_vertical_frames":1620,
        "no_interpolation":True,
        "editorial_cards_not_gameplay":True
    }
    (a.outdir/"flagship-provenance.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(json.dumps(manifest["output_sha256"],indent=2))

if __name__=="__main__":
    main()
